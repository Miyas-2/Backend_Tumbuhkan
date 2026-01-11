from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# Create async engine untuk PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

# Dependency untuk get db session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Function untuk create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Function untuk drop tables (untuk development)
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def init_growth_configs():
    """Seed initial growth configuration data if table is empty"""
    from app.models.database.plant import GrowthStageConfig
    from sqlalchemy import select

    initial_configs = [
        {"stage_name": "Stage 01: Early Growth", "tds_target": 600.0, "ph_target": 6.0, "tds_tolerance": 50.0, "ph_tolerance": 0.2},
        {"stage_name": "Stage 02: Leafy Growth", "tds_target": 800.0, "ph_target": 6.0, "tds_tolerance": 50.0, "ph_tolerance": 0.2},
        {"stage_name": "Stage 03: Head Formation", "tds_target": 1000.0, "ph_target": 6.0, "tds_tolerance": 50.0, "ph_tolerance": 0.2},
        {"stage_name": "Stage 04: Harvest Stage", "tds_target": 1100.0, "ph_target": 6.0, "tds_tolerance": 50.0, "ph_tolerance": 0.2}
    ]

    async with AsyncSessionLocal() as session:
        try:
            for config_data in initial_configs:
                stmt = select(GrowthStageConfig).where(GrowthStageConfig.stage_name == config_data["stage_name"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    print(f"🌱 Seeding config for: {config_data['stage_name']}")
                    new_config = GrowthStageConfig(**config_data)
                    session.add(new_config)
            
            await session.commit()
            print("✅ Growth configs initialized")
        except Exception as e:
            print(f"❌ Error seeding growth configs: {e}")
            await session.rollback()