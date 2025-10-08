from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "App API"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class config:
        env_file = ".env"
        

settings = Settings()