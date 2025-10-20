from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    PROJECT_NAME: str = "App API"
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    SECRET_KEY : str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        

settings = Settings()  # type: ignore[call-arg]