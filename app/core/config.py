from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Good Morning"
    VERSION: str = "25.05.02"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "hch3154"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_DB: str = "mhp_db"
    SQLALCHEMY_DATABASE_URL: Optional[str] = None

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "docker/firebase-adminsdk.json"

    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URL:
            return self.SQLALCHEMY_DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True

settings = Settings()
settings.SQLALCHEMY_DATABASE_URL = settings.get_database_url

@lru_cache()
def get_settings():
    return Settings() 