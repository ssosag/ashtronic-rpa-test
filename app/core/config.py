from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Portal Hiruko
    portal_url: str = "https://prodiagnosticotest.hiruko.com.co"
    portal_user: str
    portal_password: str

    # Database
    database_url: str = "postgresql+asyncpg://ashtronic:ashtronic@db:5432/ashtronic_rpa"

    # Selenium
    selenium_hub_url: str = "http://selenium:4444/wd/hub"
    selenium_timeout: int = 30

    # App
    log_level: str = "INFO"
    screenshots_dir: str = "/app/artifacts/screenshots"

    @model_validator(mode="after")
    def normalize_database_url(self) -> "Settings":
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
