from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# create the async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,    
)

#create the async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for declarative models
Base = declarative_base()

#Dependency that provides a database session
async def get_db():
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

#Import all models to ensure they are registered with the Base metadata
async def import_models():
    from app.models.database import sensor, actuator
    # Import other models as needed
    
# Function to create all tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#function to drop all tables (use with caution)
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)