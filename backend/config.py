import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Voice AI Knowledge Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Provider Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    
    # Workspace
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", "./workspace")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
