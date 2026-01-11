-- ============================================================
-- TUMBUHKAN DATABASE MIGRATION
-- Menyesuaikan struktur database dengan ESP32 sensor/actuator
-- ============================================================

-- ============================================================
-- SENSOR READINGS TABLE
-- ============================================================

-- Drop existing table if you want to start fresh (CAUTION: removes data!)
-- DROP TABLE IF EXISTS sensor_readings;

-- Create new sensor_readings table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- pH sensor
    ph FLOAT,
    ph_voltage FLOAT,
    
    -- TDS sensor
    tds FLOAT,
    tds_voltage FLOAT,
    
    -- Temperature sensors
    temp_air FLOAT,          -- DS18B20 - water temperature
    temp_udara FLOAT,        -- DHT22 - air temperature
    
    -- Humidity (DHT22)
    humidity FLOAT,
    
    -- LDR sensor
    ldr INTEGER,
    
    -- Ultrasonic distance sensor
    distance FLOAT,
    
    -- Flow sensor
    flow FLOAT
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
ON sensor_readings(timestamp DESC);

-- ============================================================
-- GROWTH LOGS TABLE
-- ============================================================

-- Create new growth_logs table
CREATE TABLE IF NOT EXISTS growth_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Growth stage from ML model
    growth_stage JSONB,
    
    -- Image paths
    image_path VARCHAR(255),
    annotated_image_path VARCHAR(255)
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_growth_logs_timestamp 
ON growth_logs(timestamp DESC);


-- ============================================================
-- ACTUATOR LOGS TABLE
-- ============================================================

-- Drop existing table if you want to start fresh (CAUTION: removes data!)
-- DROP TABLE IF EXISTS actuator_logs;

-- Create new actuator_logs table
CREATE TABLE IF NOT EXISTS actuator_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- LED & FAN (ON/OFF string)
    led VARCHAR(10) DEFAULT 'OFF',
    fan VARCHAR(10) DEFAULT 'OFF',
    
    -- Relay pumps (ON/OFF) - Matches ESP32 'status' payload
    ph_up BOOLEAN NOT NULL DEFAULT FALSE,
    ab_mix BOOLEAN NOT NULL DEFAULT FALSE,
    ph_down BOOLEAN NOT NULL DEFAULT FALSE,
    pump BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_actuator_logs_timestamp 
ON actuator_logs(timestamp DESC);
