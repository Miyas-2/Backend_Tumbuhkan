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
from app.models.schemas.actuator import ActuatorStatus

settings = get_settings()

class MQTTService:
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
            client.subscribe(settings.MQTT_TOPIC_SENSOR)
            client.subscribe(settings.MQTT_TOPIC_ACTUATOR_STATUS)
            print(f"📡 Subscribed to: {settings.MQTT_TOPIC_SENSOR}")
            print(f"📡 Subscribed to: {settings.MQTT_TOPIC_ACTUATOR_STATUS}")
        else:
            print(f"❌ Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received - store latest data only"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Store latest data (overwrite previous)
            if topic == settings.MQTT_TOPIC_SENSOR:
                self.latest_sensor = SensorData(**payload)
                print(f"📥 Sensor data updated: pH={payload.get('ph')}, TDS={payload.get('tds')}")
            
            elif topic == settings.MQTT_TOPIC_ACTUATOR_STATUS:
                self.latest_actuator = ActuatorStatus(**payload)
                print(f"📥 Actuator data updated: LED={payload.get('led')}, Fan={payload.get('fan')}")
                
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
                await repo.create(self.latest_actuator)
                
                print(f"💾 Actuator data saved: LED={self.latest_actuator.led}, Fan={self.latest_actuator.fan}")
                
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
    
    def publish_actuator_control(self, actuator_data: ActuatorStatus):
        """Publish actuator control to MQTT"""
        try:
            payload = json.dumps(actuator_data.model_dump())
            self.client.publish(settings.MQTT_TOPIC_ACTUATOR_STATUS, payload)
            print(f"📤 Published actuator control: {payload}")
            return True
        except Exception as e:
            print(f"❌ Error publishing actuator control: {e}")
            return False
    
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