from pathlib import Path

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):

    APP_NAME: str = "DuckyGym"

    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = Field(...)

    SECRET_KEY: str = Field(...)

    INITIAL_ADMIN_PASSWORD: str = Field(...)

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(

        env_file=(BASE_DIR / ".env", BASE_DIR / "app" / ".env"),

        env_file_encoding="utf-8",

        extra="ignore",

    )

settings = Settings()  # type: ignore[call-arg]
