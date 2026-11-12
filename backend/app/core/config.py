from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Gym Management"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "mysql+pymysql://root:182007@localhost:3306/club_management"
    SECRET_KEY: str = "supersecretkey1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=(".env", "app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()