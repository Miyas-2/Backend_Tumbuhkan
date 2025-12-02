from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    
    # MQTT
    MQTT_BROKER: str
    MQTT_PORT: int
    MQTT_TOPIC_SENSOR: str
    MQTT_TOPIC_ACTUATOR: str
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
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()