from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
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
    
    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # AWS S3 settings (used by media upload)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_DEFAULT_REGION: str | None = None
    AWS_S3_BUCKET_NAME: str | None = None
    BUCKET_NAME: str | None = None
    ENVIRONMENT: str | None = None
    S3_PRESIGN_EXPIRES: int = 3600  # seconds
        

settings = Settings()  # type: ignore[call-arg]
print("in settings", settings.DATABASE_URL)
print("in settings", settings.TEST_DATABASE_URL)