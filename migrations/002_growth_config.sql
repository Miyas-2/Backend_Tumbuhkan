-- ============================================================
-- GROWTH STAGE CONFIGURATION
-- Stores dynamic thresholds for each growth stage
-- ============================================================

CREATE TABLE IF NOT EXISTS growth_stage_configs (
    id SERIAL PRIMARY KEY,
    
    -- Stage name must match the output string from ML model
    -- e.g. "Stage 01: Early Growth"
    stage_name VARCHAR(100) UNIQUE NOT NULL,
    
    -- Thresholds for Automation
    tds_target FLOAT NOT NULL,
    tds_tolerance FLOAT DEFAULT 50.0,
    
    ph_target FLOAT NOT NULL,
    ph_tolerance FLOAT DEFAULT 0.2,
    
    -- Environmental Thresholds
    temp_threshold_high FLOAT DEFAULT 30.0,
    ldr_threshold_dark INTEGER DEFAULT 500,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEED DATA
-- Populate with default values from the previous code
-- ============================================================

INSERT INTO growth_stage_configs (stage_name, tds_target, ph_target, tds_tolerance, ph_tolerance)
VALUES 
    ('Stage 01: Early Growth', 600.0, 6.0, 50.0, 0.2),
    ('Stage 02: Leafy Growth', 800.0, 6.0, 50.0, 0.2),
    ('Stage 03: Head Formation', 1000.0, 6.0, 50.0, 0.2),
    ('Stage 04: Harvest Stage', 1100.0, 6.0, 50.0, 0.2)
ON CONFLICT (stage_name) DO UPDATE 
SET 
    tds_target = EXCLUDED.tds_target,
    ph_target = EXCLUDED.ph_target;
