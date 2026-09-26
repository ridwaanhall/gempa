"""Application settings, loaded from environment variables (and `.env` locally).

`BMKG_API` is a secret: it is only ever used server-side to reach the upstream
feeds and is never rendered into HTML, JSON responses, logs, or error messages.
"""

from functools import lru_cache

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bmkg_api: SecretStr = Field(validation_alias="BMKG_API")
    """Base URL of the upstream BMKG feed bucket. Secret."""

    debug: bool = Field(default=False, validation_alias="DEBUG")
    site_url: HttpUrl = Field(
        default=HttpUrl("https://gempa.rone.dev"), validation_alias="SITE_URL"
    )

    upstream_timeout: float = 10.0
    """Seconds before an upstream request is abandoned."""

    @property
    def bmkg_base(self) -> str:
        return self.bmkg_api.get_secret_value().rstrip("/")

    @property
    def site_origin(self) -> str:
        return str(self.site_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
