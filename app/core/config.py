from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
   
    model_config = SettingsConfigDict(
        env_file=".env",              
        env_file_encoding="utf-8",
        case_sensitive=False
    )


    DATABASE_URL: str = "postgresql+asyncpg://mdf:falldemba@localhost:5433/dataaccess_db"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    APP_NAME: str = "DataAccess API"
    API_V1_PREFIX: str = "/api/v1"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30    
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7       


def get_settings():
    return Settings()

settings = get_settings()