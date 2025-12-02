import asyncio
import json
from threading import Thread
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
    
    def set_event_loop(self, loop):
        """Set asyncio event loop dari main application"""
        self.loop = loop
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✅ Connected to MQTT Broker: {settings.MQTT_BROKER}")
            self.connected = True
            # Subscribe to topics
            client.subscribe(settings.MQTT_TOPIC_SENSOR)
            client.subscribe(settings.MQTT_TOPIC_ACTUATOR)
            print(f"📡 Subscribed to: {settings.MQTT_TOPIC_SENSOR}")
            print(f"📡 Subscribed to: {settings.MQTT_TOPIC_ACTUATOR}")
        else:
            print(f"❌ Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Handle sensor data
            if topic == settings.MQTT_TOPIC_SENSOR:
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.save_sensor_data(payload), 
                        self.loop
                    )
            
            # Handle actuator status
            elif topic == settings.MQTT_TOPIC_ACTUATOR:
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.save_actuator_status(payload),
                        self.loop
                    )
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def save_sensor_data(self, payload: dict):
        """Save sensor data to database"""
        try:
            async with AsyncSessionLocal() as db:
                sensor_data = SensorData(**payload)
                repo = SensorRepository(db)
                await repo.create(sensor_data)
                print(f"💾 Sensor data saved: pH={payload.get('ph')}, TDS={payload.get('tds')}")
        except Exception as e:
            print(f"❌ Error saving sensor data: {e}")
    
    async def save_actuator_status(self, payload: dict):
        """Save actuator status to database"""
        try:
            async with AsyncSessionLocal() as db:
                actuator_data = ActuatorStatus(**payload)
                repo = ActuatorRepository(db)
                await repo.create(actuator_data)
                print(f"💾 Actuator status saved: LED={payload.get('led')}, Fan={payload.get('fan')}")
        except Exception as e:
            print(f"❌ Error saving actuator status: {e}")
    
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
            self.client.publish(settings.MQTT_TOPIC_ACTUATOR, payload)
            print(f"📤 Published actuator control: {payload}")
            return True
        except Exception as e:
            print(f"❌ Error publishing actuator control: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("👋 Disconnected from MQTT broker")

# Singleton instance
mqtt_service = MQTTService()