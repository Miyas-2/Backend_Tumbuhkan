-- ============================================================
-- DISEASE DETECTION LOGS TABLE
-- Stores disease detection results from ML model
-- ============================================================

-- Create disease_logs table (similar structure to growth_logs)
CREATE TABLE IF NOT EXISTS disease_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Disease detection result from ML model
    -- Example: {"disease_class": "Bacterial Leaf Spot", "confidence": 0.95, "is_healthy": false}
    disease_result JSONB,
    
    -- Image paths
    image_path VARCHAR(255),
    annotated_image_path VARCHAR(255)
);

-- Create index for faster timestamp queries
CREATE INDEX IF NOT EXISTS idx_disease_logs_timestamp 
ON disease_logs(timestamp DESC);

-- ============================================================
-- OPTIONAL: Add column for linking to sensor data
-- ============================================================
-- ALTER TABLE disease_logs ADD COLUMN sensor_reading_id BIGINT REFERENCES sensor_readings(id);
