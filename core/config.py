from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    PROJECT_NAME: str = "App API"
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    SECRET_KEY : str
    # SMTP / Mailer settings (used by core.mailer)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        

settings = Settings()  # type: ignore[call-arg]