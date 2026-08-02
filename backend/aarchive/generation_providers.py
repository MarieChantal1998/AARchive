from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    image_factory: Callable[[Path], Any]
    audio_factory: Callable[[Path], Any]
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
            image_factory=lambda _output_dir: GMICloudImageProvider(api_key=settings.gmi_api_key),
            audio_factory=lambda _output_dir: GMICloudAudioProvider(api_key=settings.gmi_api_key),
            image_params={"aspect_ratio": "16:9"},
            audio_params={},
        )
    if provider == "nvidia":
        if not settings.nvidia_api_key:
            raise ProviderConfigurationError("A free NVIDIA NIM API key is not configured")
        from genblaze_nvidia import NvidiaImageProvider

        from .nvidia_compat import NvidiaHostedMagpieAudioProvider

        return GenerationProvider(
            slug="nvidia",
            display_name="NVIDIA NIM through Genblaze",
            image_model=settings.nvidia_image_model,
            audio_model=settings.nvidia_audio_model,
            image_factory=lambda output_dir: NvidiaImageProvider(
                api_key=settings.nvidia_api_key, output_dir=output_dir
            ),
            audio_factory=lambda output_dir: NvidiaHostedMagpieAudioProvider(
                api_key=settings.nvidia_api_key,
                output_dir=output_dir,
                synthesize_url=settings.nvidia_tts_synthesize_url,
                voices_url=settings.nvidia_tts_voices_url,
            ),
            image_params={"width": 1024, "height": 576, "steps": 4},
            audio_params={
                "language": "en-US",
                "voice": "Magpie-Multilingual.EN-US.Aria",
                "encoding": "LINEAR_PCM",
                "sample_rate_hz": 44100,
            },
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
            image_factory=lambda _output_dir: DalleProvider(api_key=settings.openai_api_key),
            audio_factory=lambda _output_dir: OpenAITTSProvider(api_key=settings.openai_api_key),
            image_params={"size": "1536x1024", "quality": "medium"},
            audio_params={
                "voice": settings.openai_tts_voice,
                "response_format": "mp3",
                "instructions": "Calm, concise professional training facilitator; neutral and observational.",
            },
        )
    raise ProviderConfigurationError(f"Unsupported generation provider: {settings.generation_provider}")
