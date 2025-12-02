from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database - PostgreSQL
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # MQTT
    MQTT_BROKER: str
    MQTT_PORT: int
    MQTT_TOPIC_SENSOR: str
    MQTT_TOPIC_ACTUATOR_STATUS: str
    MQTT_SAVE_INTERVAL: int
    
    # AI Services
    GEMINI_API_KEY: str
    HF_MODEL_NAME: str
    HF_TOKEN: str = ""
    
    # Application
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = True
    API_PREFIX: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()