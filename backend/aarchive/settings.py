from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origins: str = "http://localhost:3000"
    max_upload_mb: int = Field(default=500, ge=1, le=5000)
    processing_timeout_seconds: int = 900
    generation_timeout_seconds: int = 180

    b2_endpoint_url: str = "https://s3.us-west-004.backblazeb2.com"
    b2_region: str = "us-west-004"
    b2_bucket: str = ""
    b2_key_id: str = ""
    b2_app_key: str = ""
    b2_public_url_base: str = ""

    openai_api_key: str = ""
    openai_transcription_model: str = "gpt-4o-mini-transcribe"
    openai_analysis_model: str = "gpt-4.1-mini"
    openai_image_model: str = "gpt-image-1"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "coral"

    demo_project_id: str = "demo-coordinated-response"
    demo_video_url: str = ""
    demo_cover_url: str = ""
    demo_narration_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def b2_configured(self) -> bool:
        return bool(self.b2_bucket and self.b2_key_id and self.b2_app_key)

    @property
    def generation_configured(self) -> bool:
        return self.b2_configured and bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

