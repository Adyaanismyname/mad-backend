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
    
    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # AWS S3 Settings for Media Storage
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET_NAME: str
    AWS_CLOUDFRONT_DOMAIN: str | None = None  # Optional: Use CloudFront for better performance
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
        

settings = Settings()  # type: ignore[call-arg]
print("in settings", settings.DATABASE_URL)
print("in settings", settings.TEST_DATABASE_URL)