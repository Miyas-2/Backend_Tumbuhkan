# Tumbuhkan Backend

Backend system untuk IoT Hydroponic plant monitoring dengan ESP32.

## Features
- 🌱 **Sensor Data Management** - pH, TDS, Temperature, Humidity, LDR, Distance, Flow
- 📡 **MQTT Integration** - Real-time sensor data & relay control
- 🎛️ **Relay Control API** - LED, FAN, PH_UP, AB_MIX, PH_DOWN, PUMP
- 🤖 **Computer Vision** - Plant disease detection
- 📊 **Prediction Model** - Random Forest untuk prediksi kondisi tanaman
- 💬 **RAG Chatbot** - Gemini AI & HuggingFace embeddings

## Architecture

```
Frontend → API → MQTT → ESP32
    ↑                    ↓
    └──────── Database ←─┘
```

## Tech Stack
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL
- **Message Broker**: MQTT (broker.mqtt.cool)
- **Hardware**: ESP32 + Sensors
- **AI**: Google Gemini AI, HuggingFace Transformers

## MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `tumbuhkan/sensor/data` | ESP32 → Backend | Sensor readings (pH, TDS, temperature, etc.) |
| `tumbuhkan/relay/control` | Backend → ESP32 | Relay control commands |
| `tumbuhkan/relay/status` | ESP32 → Backend | Current relay states |
| `tumbuhkan/ph/calibration` | Backend → ESP32 | pH sensor calibration |
| `tumbuhkan/tds/calibration` | Backend → ESP32 | TDS sensor calibration |

## API Endpoints

### Relay Control

```http
# Full control
POST /api/v1/actuators/control
{
    "LED": {"state": "ON"},
    "FAN": {"state": "OFF"},
    "PH_UP": {"duration": 5000},
    "PUMP": {"duration": 10000}
}

# Quick controls
POST /api/v1/actuators/led/ON
POST /api/v1/actuators/fan/OFF
POST /api/v1/actuators/pump/PH_UP/5000

# Get status
GET /api/v1/actuators/status/live    # Real-time from MQTT
GET /api/v1/actuators/latest         # From database
GET /api/v1/actuators/history        # Historical logs
```

### Sensor Data

```http
GET /api/v1/sensors/latest           # Latest reading
GET /api/v1/sensors/live             # Real-time from MQTT
GET /api/v1/sensors/history          # Historical data
```

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Setup database:**
```bash
# Run migration
psql -d tumbuhkan_db -f migrations/001_esp32_schema.sql
```

4. **Run development server:**
```bash
uvicorn app.main:app --reload
```

## Database Schema

### sensor_readings
| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key |
| timestamp | DATETIME | Reading time |
| ph | FLOAT | pH value |
| ph_voltage | FLOAT | pH sensor voltage |
| tds | FLOAT | TDS in ppm |
| tds_voltage | FLOAT | TDS sensor voltage |
| temp_air | FLOAT | Water temperature (DS18B20) |
| temp_udara | FLOAT | Air temperature (DHT22) |
| humidity | FLOAT | Air humidity |
| ldr | INT | Light sensor value |
| distance | FLOAT | Ultrasonic distance (cm) |
| flow | FLOAT | Water flow (L/min) |

### actuator_logs
| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key |
| timestamp | DATETIME | Action time |
| led | VARCHAR | LED state (ON/OFF) |
| fan | VARCHAR | FAN state (ON/OFF) |
| ph_up | BOOL | PH_UP relay active |
| ph_up_duration | INT | Duration in ms |
| ab_mix | BOOL | AB_MIX relay active |
| ab_mix_duration | INT | Duration in ms |
| ph_down | BOOL | PH_DOWN relay active |
| ph_down_duration | INT | Duration in ms |
| pump | BOOL | PUMP relay active |
| pump_duration | INT | Duration in ms |

## ESP32 Integration

The backend is designed to work with ESP32 running the `main_esp32.ino` code.

### Relay Control Format
```json
// LED & FAN - state only
{"LED": {"state": "ON"}}
{"FAN": {"state": "OFF"}}

// Pumps - duration in milliseconds
{"PH_UP": {"duration": 5000}}
{"AB_MIX": {"duration": 3000}}
{"PH_DOWN": {"duration": 2000}}
{"PUMP": {"duration": 10000}}
```

### Sensor Data Format (from ESP32)
```json
{
    "ph": 6.5,
    "ph_voltage": 1.8,
    "tds": 800,
    "tds_voltage": 1.2,
    "temp_air": 25.5,
    "temp_udara": 28.0,
    "humidity": 65.0,
    "ldr": 2048,
    "distance": 15.5,
    "flow": 2.5
}
```

## API Documentation
After running the server, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
