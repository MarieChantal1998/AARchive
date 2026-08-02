from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origins: str = "http://localhost:3000"
    max_upload_mb: int = Field(default=500, ge=1, le=5000)
    processing_timeout_seconds: int = 900
    generation_timeout_seconds: int = 480

    b2_endpoint_url: str = "https://s3.us-west-004.backblazeb2.com"
    b2_region: str = "us-west-004"
    b2_bucket: str = ""
    b2_key_id: str = ""
    b2_app_key: str = ""
    b2_public_url_base: str = ""

    transcription_provider: str = "local_whisper"
    local_whisper_model: str = "tiny.en"
    analysis_provider: str = "local"

    generation_provider: str = "gmicloud"
    generation_mode: str = "cached_only"

    local_image_model: str = "pillow-lesson-card-v1"
    local_audio_model: str = "macos-say-tts-v1"
    local_tts_voice: str = "Samantha"
    local_tts_rate: int = 155

    gmi_api_key: str = ""
    gmi_text_model: str = "deepseek-ai/DeepSeek-V3"
    gmi_image_model: str = "seedream-5.0-lite"
    gmi_audio_model: str = "elevenlabs-tts-v3"
    gmi_audio_voice: str = "Rachel"

    nvidia_api_key: str = ""
    nvidia_image_model: str = "black-forest-labs/flux.1-schnell"
    nvidia_audio_model: str = "nvidia/magpie-tts-multilingual"
    nvidia_http_timeout_seconds: int = 360
    nvidia_tts_synthesize_url: str = (
        "https://877104f7-e885-42b9-8de8-f6e4c6303969.invocation.api.nvcf.nvidia.com"
        "/v1/audio/synthesize"
    )
    nvidia_tts_voices_url: str = (
        "https://877104f7-e885-42b9-8de8-f6e4c6303969.invocation.api.nvcf.nvidia.com"
        "/v1/audio/list_voices"
    )
    nvidia_tts_one_shot_enabled: bool = False
    nvidia_tts_one_shot_project_id: str = "35fbaf01-8ecc-4b9c-a848-e1b59ecae00f"
    nvidia_tts_one_shot_brief_id: str = "8eb28934-d786-5dc2-b134-12dc027e3d23"

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
        if not self.b2_configured:
            return False
        if self.generation_provider.lower() == "local":
            return True
        return bool(self.generation_api_key)

    @property
    def generation_api_key(self) -> str:
        provider = self.generation_provider.lower()
        if provider == "gmicloud":
            return self.gmi_api_key
        if provider == "nvidia":
            return self.nvidia_api_key
        if provider == "openai":
            return self.openai_api_key
        return ""

    @property
    def generation_can_run(self) -> bool:
        return self.generation_mode == "generate_once" and self.generation_configured


@lru_cache
def get_settings() -> Settings:
    return Settings()
