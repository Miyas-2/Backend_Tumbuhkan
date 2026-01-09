import asyncio
import json
from datetime import datetime
from typing import Optional
from paho.mqtt import client as mqtt_client
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.repositories.sensor_repo import SensorRepository
from app.repositories.actuator_repo import ActuatorRepository
from app.models.schemas.sensor import SensorData
from app.models.schemas.actuator import ActuatorStatus, RelayControlRequest, ActuatorLogCreate

settings = get_settings()

class MQTTService:
    # Topics sesuai ESP32
    TOPIC_SENSOR = "tumbuhkan/sensor/data"
    TOPIC_RELAY_CONTROL = "tumbuhkan/relay/control"
    TOPIC_RELAY_STATUS = "tumbuhkan/relay/status"
    TOPIC_PH_CALIBRATION = "tumbuhkan/ph/calibration"
    TOPIC_TDS_CALIBRATION = "tumbuhkan/tds/calibration"
    
    def __init__(self):
        self.client = mqtt_client.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False
        self.loop = None
        
        # Store only latest data
        self.latest_sensor: Optional[SensorData] = None
        self.latest_actuator: Optional[ActuatorStatus] = None
        self.batch_task: Optional[asyncio.Task] = None
    
    def set_event_loop(self, loop):
        """Set asyncio event loop dari main application"""
        self.loop = loop
        # Start batch save task
        if self.batch_task is None and self.loop:
            self.batch_task = asyncio.run_coroutine_threadsafe(
                self.batch_save_worker(), 
                self.loop
            )
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✅ Connected to MQTT Broker: {settings.MQTT_BROKER}")
            self.connected = True
            # Subscribe to sensor data and relay status
            client.subscribe(self.TOPIC_SENSOR)
            client.subscribe(self.TOPIC_RELAY_STATUS)
            print(f"📡 Subscribed to: {self.TOPIC_SENSOR}")
            print(f"📡 Subscribed to: {self.TOPIC_RELAY_STATUS}")
        else:
            print(f"❌ Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received - store latest data only"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Store latest sensor data
            if topic == self.TOPIC_SENSOR:
                self.latest_sensor = SensorData(**payload)
                print(f"📥 Sensor data updated: pH={payload.get('ph')}, TDS={payload.get('tds')}")
            
            # Store latest actuator status
            elif topic == self.TOPIC_RELAY_STATUS:
                self.latest_actuator = ActuatorStatus(**payload)
                print(f"📥 Relay status updated: LED={payload.get('LED')}, FAN={payload.get('FAN')}")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def batch_save_worker(self):
        """Background worker to save latest data every N seconds"""
        print(f"🕐 Batch save worker started (interval: {settings.MQTT_SAVE_INTERVAL}s)")
        
        while True:
            try:
                await asyncio.sleep(settings.MQTT_SAVE_INTERVAL)
                
                # Save only if data exists
                if self.latest_sensor:
                    await self.save_sensor_data()
                
                if self.latest_actuator:
                    await self.save_actuator_data()
                    
            except Exception as e:
                print(f"❌ Error in batch save worker: {e}")
    
    async def save_sensor_data(self):
        """Save latest sensor data to database"""
        try:
            if not self.latest_sensor:
                return
            
            async with AsyncSessionLocal() as db:
                repo = SensorRepository(db)
                await repo.create(self.latest_sensor)
                
                print(f"💾 Sensor data saved: pH={self.latest_sensor.ph}, TDS={self.latest_sensor.tds}")
                
                # Clear after save
                self.latest_sensor = None
                
        except Exception as e:
            print(f"❌ Error saving sensor data: {e}")
    
    async def save_actuator_data(self):
        """Save latest actuator data to database"""
        try:
            if not self.latest_actuator:
                return
            
            async with AsyncSessionLocal() as db:
                repo = ActuatorRepository(db)
                
                # Convert ActuatorStatus to ActuatorLogCreate
                log_data = ActuatorLogCreate(
                    led=self.latest_actuator.LED,
                    fan=self.latest_actuator.FAN,
                    ph_up=self.latest_actuator.PH_UP == "ON",
                    ab_mix=self.latest_actuator.AB_MIX == "ON",
                    ph_down=self.latest_actuator.PH_DOWN == "ON",
                    pump=self.latest_actuator.PUMP == "ON"
                )
                
                await repo.create(log_data)
                
                print(f"💾 Actuator data saved: LED={self.latest_actuator.LED}, FAN={self.latest_actuator.FAN}")
                
                # Clear after save
                self.latest_actuator = None
                
        except Exception as e:
            print(f"❌ Error saving actuator data: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ Error connecting to MQTT: {e}")
    
    def publish_relay_control(self, relay_control: RelayControlRequest) -> bool:
        """Publish relay control command to ESP32
        
        Format yang dikirim ke topic tumbuhkan/relay/control:
        {
            "LED": {"state": "ON"},
            "FAN": {"state": "OFF"},
            "PH_UP": {"duration": 5000},
            "AB_MIX": {"duration": 3000}
        }
        """
        try:
            # Build payload hanya untuk relay yang diset
            payload = {}
            
            if relay_control.LED:
                payload["LED"] = {"state": relay_control.LED.state}
            
            if relay_control.FAN:
                payload["FAN"] = {"state": relay_control.FAN.state}
            
            if relay_control.PUMP:
                payload["PUMP"] = {"duration": relay_control.PUMP.duration}

            if relay_control.PH_UP:
                payload["PH_UP"] = {"duration": relay_control.PH_UP.duration}
            
            if relay_control.AB_MIX:
                payload["AB_MIX"] = {"duration": relay_control.AB_MIX.duration}
            
            if relay_control.PH_DOWN:
                payload["PH_DOWN"] = {"duration": relay_control.PH_DOWN.duration}
            
            if not payload:
                print("⚠️ No relay control data to publish")
                return False
            
            json_payload = json.dumps(payload)
            result = self.client.publish(self.TOPIC_RELAY_CONTROL, json_payload)
            
            if result.rc == 0:
                print(f"📤 Published relay control: {json_payload}")
                return True
            else:
                print(f"❌ Failed to publish relay control, rc={result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Error publishing relay control: {e}")
            return False
    
    def publish_ph_calibration(self, v4: float = None, v7: float = None, v9: float = None) -> bool:
        """Publish pH calibration data"""
        try:
            payload = {}
            if v4 is not None:
                payload["v4"] = v4
            if v7 is not None:
                payload["v7"] = v7
            if v9 is not None:
                payload["v9"] = v9
            
            if not payload:
                return False
            
            json_payload = json.dumps(payload)
            result = self.client.publish(self.TOPIC_PH_CALIBRATION, json_payload)
            print(f"📤 Published pH calibration: {json_payload}")
            return result.rc == 0
            
        except Exception as e:
            print(f"❌ Error publishing pH calibration: {e}")
            return False
    
    def publish_tds_calibration(self, m: float = None, c: float = None, ppm: int = None) -> bool:
        """Publish TDS calibration data (fast or legacy mode)"""
        try:
            payload = {}
            
            # Fast calibration mode
            if m is not None and c is not None:
                payload["m"] = m
                payload["c"] = c
            # Legacy 2-point calibration
            elif ppm is not None:
                payload["ppm"] = ppm
            else:
                return False
            
            json_payload = json.dumps(payload)
            result = self.client.publish(self.TOPIC_TDS_CALIBRATION, json_payload)
            print(f"📤 Published TDS calibration: {json_payload}")
            return result.rc == 0
            
        except Exception as e:
            print(f"❌ Error publishing TDS calibration: {e}")
            return False
    
    def get_latest_sensor(self) -> Optional[SensorData]:
        """Get latest sensor data (from memory, not database)"""
        return self.latest_sensor
    
    def get_latest_actuator_status(self) -> Optional[ActuatorStatus]:
        """Get latest actuator status (from memory, not database)"""
        return self.latest_actuator
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        # Cancel batch task
        if self.batch_task:
            self.batch_task.cancel()
        
        self.client.loop_stop()
        self.client.disconnect()
        print("👋 Disconnected from MQTT broker")

# Singleton instance
mqtt_service = MQTTService()