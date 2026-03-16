from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "Org Structure API"

    class Config:
        env_file = ".env"

settings = Settings()
