
import asyncio
import time
from typing import Dict, Optional, Literal
from app.services.mqtt_service import mqtt_service
from app.models.schemas.sensor import SensorData
from app.models.schemas.actuator import RelayControlRequest, PumpControl, LedFanControl, LedFanControl, ActuatorLogCreate
from app.repositories.actuator_repo import ActuatorRepository
from app.repositories.actuator_repo import ActuatorRepository
from app.repositories.sensor_repo import SensorRepository
from app.repositories.growth_repo import GrowthRepository
from app.core.database import AsyncSessionLocal
from app.core.config import get_settings

settings = get_settings()

class AutomationService:
    """
    Service untuk mengelola logika otomatisasi actuator berdasarkan sensor reading.
    Mengimplementasikan algoritma dosing iteratif (Calibration -> Calculate -> Dose -> Wait).
    """

    # --- CONFIGURATION (Bisa dipindah ke env/db nantinya) ---
    TARGET_PH = 6.0
    
    # Default Target TDS if growth unknown
    DEFAULT_TARGET_TDS = 800.0  
    TARGET_TDS = DEFAULT_TARGET_TDS # This will be updated dynamically
    
    # Dynamic Growth Targets Config
    # Format: "Class String": {"tds": value, "ph": value}
    CONFIG_GROWTH_TARGETS = {
        "Stage 01: Early Growth": {"tds": 600.0, "ph": 6.0},
        "Stage 02: Leafy Growth": {"tds": 800.0, "ph": 6.0},
        "Stage 03: Head Formation": {"tds": 1000.0, "ph": 6.0},
        "Stage 04: Harvest Stage": {"tds": 1100.0, "ph": 6.0}
    }
    
    PH_TOLERANCE = 0.2
    TDS_TOLERANCE = 50.0 # PPM
    
    LDR_THRESHOLD_DARK = 500 # Contoh nilai
    TEMP_THRESHOLD_HIGH = 30.0
    
    # Pump Config
    FLOW_RATE_ML_PER_SEC = 2.0  # Estimasi flow rate pompa (perlu kalibrasi real)
    CALIBRATION_DOSE_ML = 5.0   # Dosis kecil untuk test
    
    MIXING_TIME_SEC = 60        # Waktu tunggu pencampuran air
    
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # State Machine Variables
        self.ph_state: Literal["IDLE", "CALIBRATING", "DOSING", "MIXING"] = "IDLE"
        self.tds_state: Literal["IDLE", "CALIBRATING", "DOSING", "MIXING"] = "IDLE"
        
        # pH Logic Memory
        self.ph_last_value = 0.0
        self.ph_ppm_per_ml = 0.0 # Sensitivity (change per ml)
        self.ph_wait_until = 0   # Timestamp for mixing wait
        
        # TDS Logic Memory
        self.tds_last_value = 0.0
        self.tds_ppm_per_ml = 0.0
        self.tds_wait_until = 0

    def start(self):
        """Mulai automation loop background task"""
        if not self.running:
            self.running = True
            loop = asyncio.get_event_loop()
            self.task = loop.create_task(self._automation_loop())
            print("🤖 Automation Service started")

    async def stop(self):
        """Stop automation loop"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            print("🤖 Automation Service stopped")

    async def _automation_loop(self):
        """Main loop that runs every N seconds"""
        while self.running:
            try:
                # 1. Get Latest Data
                sensor_data = mqtt_service.get_latest_sensor()
                
                if sensor_data:
                    # 2. Update Dynamic Targets based on Growth Stage
                    await self._update_targets_from_growth()
                    
                    # 3. Run Logic
                    await self._control_environment(sensor_data)
                    await self._control_ph(sensor_data)
                    await self._control_nutrients(sensor_data)
                
                await asyncio.sleep(5) # Run check every 5 seconds
                
            except Exception as e:
                print(f"❌ Error in automation loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)

    async def _control_environment(self, date: SensorData):
        """Control LED and FAN based on simple thresholds"""
        controls = {}
        
        # LED Logic (LDR)
        if date.ldr is not None:
             # Jika gelap -> nyalakan lampu
             target_led = "ON" if date.ldr > self.LDR_THRESHOLD_DARK else "OFF"
             controls["LED"] = LedFanControl(state=target_led)
        
        # FAN Logic (Temperature/Humidity)
        # Prioritas suhu > kelembaban
        if date.temp_udara is not None:
            target_fan = "ON" if date.temp_udara > self.TEMP_THRESHOLD_HIGH else "OFF"
            controls["FAN"] = LedFanControl(state=target_fan)
            
        if controls:
            req = RelayControlRequest(**controls)
            # Only publish if different might be good, but MQTT usually handles idempotent
            # Untuk sekarang kirim terus tidak masalah, atau cek status terakhir di MQTT service
            mqtt_service.publish_relay_control(req)

    async def _control_ph(self, data: SensorData):
        """Advanced pH Dosing Logic"""
        if data.ph is None:
            return

        current_ph = data.ph
        current_time = time.time()
        
        # --- STATE MACHINE ---
        
        # 1. WAITING FOR MIXING
        if self.ph_state == "MIXING":
            if current_time < self.ph_wait_until:
                return # Masih mixing, do nothing
            else:
                # Mixing selesai, saatnya evaluasi
                delta_ph = abs(current_ph - self.ph_last_value)
                
                # Hitung sensitivity baru: perubahan pH per ml yang tadi disuntikkan
                # (Kita asumsikan tadi suntik CALIBRATION_DOSE_ML atau calculated dose)
                # Sederhana: update sensitivity jika perubahan signifikan
                if delta_ph > 0.05: # Noise filter
                     # TODO: Simpan 'last_dose_ml' di state agar akurat
                     pass 

                self.ph_state = "IDLE"
                print(f"🤖 pH Mixing done. Current: {current_ph}")

        # 2. IDLE - Check if action needed
        if self.ph_state == "IDLE":
            diff = current_ph - self.TARGET_PH
            
            if abs(diff) > self.PH_TOLERANCE:
                print(f"🤖 pH out of range ({current_ph}). Target: {self.TARGET_PH}")
                
                # Tentukan pompa: Up atau Down (NOTE: User request 'ph up dengan ph down')
                # Logika umum: pH tinggi -> butuh pH Down (acid). pH rendah -> butuh pH Up (base).
                pump_name = "PH_DOWN" if diff > 0 else "PH_UP"
                
                # Masuk fase kalibrasi/pulse test dulu
                self.ph_state = "CALIBRATING"
                self.ph_last_value = current_ph
                
                # Lakukan pulse kecil (5ml)
                await self._dose_pump(pump_name, self.CALIBRATION_DOSE_ML)
                
                # Set timer mixing
                self.ph_wait_until = current_time + self.MIXING_TIME_SEC
                self.ph_state = "MIXING"

    async def _control_nutrients(self, data: SensorData):
        """Advanced Nutrient (TDS) Dosing Logic"""
        if data.tds is None:
            return

        current_tds = data.tds
        current_time = time.time()
        
        # NOTE: User logic: "pump menurunkan ppm". "ab mix pasangannya dengan pump".
        # Asumsi: 
        # - TDS Rendah -> Butuh AB Mix (Naikkan PPM)
        # - TDS Tinggi -> Butuh Pump Air Baku/Air Kosong (Turunkan PPM)
        
        # 1. MIXING STATE
        if self.tds_state == "MIXING":
            if current_time < self.tds_wait_until:
                return
            else:
                # Mixing done
                # Calculate effect
                delta_tds = abs(current_tds - self.tds_last_value)
                
                # Jika perubahan cukup besar, kita bisa hitung sensitivity
                # ppm_per_ml = delta_tds / last_dose_ml
                
                self.tds_state = "IDLE"

        # 2. IDLE STATE
        if self.tds_state == "IDLE":
            diff = self.TARGET_TDS - current_tds
            
            # Jika selisih diluar toleransi
            if abs(diff) > self.TDS_TOLERANCE:
                print(f"🤖 TDS out of range ({current_tds}). Target: {self.TARGET_TDS}")
                
                # Tentukan pompa
                # diff positif (Target > Current) -> Kurang nutrisi -> AB Mix
                # diff negatif (Target < Current) -> Kelebihan nutrisi -> Tambah Air (Pump)
                pump_name = "AB_MIX" if diff > 0 else "PUMP"
                
                # Start Calibration Pulse
                self.tds_state = "CALIBRATING"
                self.tds_last_value = current_tds
                
                await self._dose_pump(pump_name, self.CALIBRATION_DOSE_ML)
                
                self.tds_wait_until = current_time + self.MIXING_TIME_SEC
                self.tds_state = "MIXING"

    async def _dose_pump(self, pump_name: str, ml_amount: float):
        """Helper to run pump for N seconds based on mL amount"""
        
        # Hitung durasi (detik)
        duration_sec = ml_amount / self.FLOW_RATE_ML_PER_SEC
        duration_ms = int(duration_sec * 1000)
        
        print(f"🤖 Dosing {pump_name}: {ml_amount}ml ({duration_ms}ms)")
        
        # Build Request
        controls = {
            pump_name: PumpControl(duration=duration_ms)
        }
        req = RelayControlRequest(**controls)
        
        # Publish
        mqtt_service.publish_relay_control(req)
        
        # Log to DB (Async but fire and forget style for now, or await)
        # Idealnya panggil repo simpan log "System Dosing"

    async def _update_targets_from_growth(self):
        """Fetch latest growth stage and update targets"""
        try:
            async with AsyncSessionLocal() as db:
                repo = GrowthRepository(db)
                growth_data = await repo.get_latest()
                
                if growth_data and growth_data.growth_stage:
                    # growth_stage is JSONB dict or str
                    growth_stage_dict = growth_data.growth_stage
                    if isinstance(growth_stage_dict, str):
                        import json
                        try:
                            growth_stage_dict = json.loads(growth_stage_dict)
                        except:
                            pass
                            
                    if isinstance(growth_stage_dict, dict):
                        growth_class = growth_stage_dict.get("growth_class")
                        
                        if growth_class in self.CONFIG_GROWTH_TARGETS:
                            config = self.CONFIG_GROWTH_TARGETS[growth_class]
                            
                            # Update Targets
                            if config.get("tds") is not None:
                                # Only log if changed
                                if self.TARGET_TDS != config["tds"]:
                                    print(f"🌱 Growth Stage detected: {growth_class}. Updating Target TDS to {config['tds']}")
                                self.TARGET_TDS = float(config["tds"])
                                
                            if config.get("ph") is not None:
                                if self.TARGET_PH != config["ph"]:
                                    print(f"🌱 Growth Stage detected: {growth_class}. Updating Target pH to {config['ph']}")
                                self.TARGET_PH = float(config["ph"])
                            
        except Exception as e:
            print(f"⚠️ Error updating growth targets: {e}")
        
# Global Instance
automation_service = AutomationService()
