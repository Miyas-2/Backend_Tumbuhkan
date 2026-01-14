"""
Script untuk generate dummy sensor data untuk testing.
Jalankan dengan: python seed_dummy_data.py
"""
import asyncio
import random
from datetime import datetime, timedelta

async def seed_sensor_data():
    from app.core.database import AsyncSessionLocal
    from app.models.database.sensor import SensorReading
    
    print("🌱 Seeding dummy sensor data...")
    
    async with AsyncSessionLocal() as db:
        # Generate data for last 7 days, every 30 minutes
        now = datetime.utcnow()
        start_time = now - timedelta(days=7)
        
        records = []
        current_time = start_time
        
        while current_time <= now:
            # Randomize sensor values with realistic ranges
            record = SensorReading(
                timestamp=current_time,
                ph=round(random.uniform(5.5, 7.5), 2),
                ph_voltage=round(random.uniform(2.0, 3.0), 2),
                tds=round(random.uniform(600, 1200), 2),
                tds_voltage=round(random.uniform(1.0, 2.0), 2),
                temp_air=round(random.uniform(24, 30), 1),      # Water temp
                temp_udara=round(random.uniform(25, 35), 1),    # Air temp
                humidity=round(random.uniform(60, 90), 1),
                ldr=random.randint(200, 800),
                distance=round(random.uniform(10, 50), 1),
                flow=round(random.uniform(1, 5), 2)
            )
            records.append(record)
            
            # Next interval (every 30 minutes)
            current_time += timedelta(minutes=30)
        
        # Bulk insert
        db.add_all(records)
        await db.commit()
        
        print(f"✅ Inserted {len(records)} sensor readings!")
        print(f"   Time range: {start_time} to {now}")

if __name__ == "__main__":
    asyncio.run(seed_sensor_data())
