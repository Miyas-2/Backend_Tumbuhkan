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
    flow FLOAT,
    
    -- Growth stage from ML model
    growth_stage VARCHAR(50)
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
ON sensor_readings(timestamp DESC);

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
    
    -- Relay pumps with duration
    ph_up BOOLEAN NOT NULL DEFAULT FALSE,
    ph_up_duration INTEGER DEFAULT 0,
    
    ab_mix BOOLEAN NOT NULL DEFAULT FALSE,
    ab_mix_duration INTEGER DEFAULT 0,
    
    ph_down BOOLEAN NOT NULL DEFAULT FALSE,
    ph_down_duration INTEGER DEFAULT 0,
    
    pump BOOLEAN NOT NULL DEFAULT FALSE,
    pump_duration INTEGER DEFAULT 0
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_actuator_logs_timestamp 
ON actuator_logs(timestamp DESC);

-- ============================================================
-- OPTIONAL: Migration from old structure
-- If you have existing data and want to migrate
-- ============================================================

-- Rename columns for sensor_readings (if migrating)
-- ALTER TABLE sensor_readings RENAME COLUMN water_flow TO flow;
-- ALTER TABLE sensor_readings RENAME COLUMN air_humidity TO humidity;
-- ALTER TABLE sensor_readings RENAME COLUMN air_temperature TO temp_udara;
-- ALTER TABLE sensor_readings RENAME COLUMN water_temperature TO temp_air;
-- ALTER TABLE sensor_readings RENAME COLUMN water_level TO distance;
-- ALTER TABLE sensor_readings RENAME COLUMN ldr_value TO ldr;
-- ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS ph_voltage FLOAT;
-- ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS tds_voltage FLOAT;

-- Rename columns for actuator_logs (if migrating)
-- ALTER TABLE actuator_logs DROP COLUMN IF EXISTS pump_nutrisi_A;
-- ALTER TABLE actuator_logs DROP COLUMN IF EXISTS pump_nutrisi_B;
-- ALTER TABLE actuator_logs DROP COLUMN IF EXISTS pump_Ph_Up;
-- ALTER TABLE actuator_logs DROP COLUMN IF EXISTS pump_Ph_Down;
-- ALTER TABLE actuator_logs ADD COLUMN IF NOT EXISTS led VARCHAR(10) DEFAULT 'OFF';
-- ALTER TABLE actuator_logs ADD COLUMN IF NOT EXISTS fan VARCHAR(10) DEFAULT 'OFF';
-- ... etc
