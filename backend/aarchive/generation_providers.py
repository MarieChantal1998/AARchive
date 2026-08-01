from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .settings import Settings


class ProviderConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationProvider:
    slug: str
    display_name: str
    image_model: str
    audio_model: str
    image_factory: Callable[[], Any]
    audio_factory: Callable[[], Any]
    image_params: dict[str, Any]
    audio_params: dict[str, Any]


def provider_for(settings: Settings) -> GenerationProvider:
    provider = settings.generation_provider.lower()
    if provider == "gmicloud":
        if not settings.gmi_api_key:
            raise ProviderConfigurationError("GMI Cloud credits and a server-side API key are not configured")
        from genblaze_gmicloud import GMICloudAudioProvider, GMICloudImageProvider

        return GenerationProvider(
            slug="gmicloud",
            display_name="GMI Cloud through Genblaze",
            image_model=settings.gmi_image_model,
            audio_model=settings.gmi_audio_model,
            image_factory=lambda: GMICloudImageProvider(api_key=settings.gmi_api_key),
            audio_factory=lambda: GMICloudAudioProvider(api_key=settings.gmi_api_key),
            image_params={"aspect_ratio": "16:9"},
            audio_params={},
        )
    if provider == "nvidia":
        if not settings.nvidia_api_key:
            raise ProviderConfigurationError("A free NVIDIA NIM API key is not configured")
        from genblaze_nvidia import NvidiaAudioProvider, NvidiaImageProvider

        return GenerationProvider(
            slug="nvidia",
            display_name="NVIDIA NIM through Genblaze",
            image_model=settings.nvidia_image_model,
            audio_model=settings.nvidia_audio_model,
            image_factory=lambda: NvidiaImageProvider(api_key=settings.nvidia_api_key),
            audio_factory=lambda: NvidiaAudioProvider(api_key=settings.nvidia_api_key),
            image_params={"aspect_ratio": "16:9"},
            audio_params={},
        )
    if provider == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("An explicitly funded OpenAI API key is not configured")
        from genblaze_openai import DalleProvider, OpenAITTSProvider

        return GenerationProvider(
            slug="openai",
            display_name="OpenAI through Genblaze (optional)",
            image_model=settings.openai_image_model,
            audio_model=settings.openai_tts_model,
            image_factory=lambda: DalleProvider(api_key=settings.openai_api_key),
            audio_factory=lambda: OpenAITTSProvider(api_key=settings.openai_api_key),
            image_params={"size": "1536x1024", "quality": "medium"},
            audio_params={
                "voice": settings.openai_tts_voice,
                "response_format": "mp3",
                "instructions": "Calm, concise professional training facilitator; neutral and observational.",
            },
        )
    raise ProviderConfigurationError(f"Unsupported generation provider: {settings.generation_provider}")

