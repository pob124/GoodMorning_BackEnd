from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "FastAPI App"
    DEBUG: bool = True
    FIREBASE_CREDENTIALS_PATH: str = "docker/firebase-adminsdk.json"
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/mhp_db"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 