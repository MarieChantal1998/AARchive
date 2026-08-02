"""Compatibility adapter for NVIDIA's hosted Magpie TTS trial endpoint.

Genblaze's NVIDIA audio provider currently targets the generic ``/genai``
surface. NVIDIA moved hosted Magpie Multilingual TTS to its Riva-compatible
multipart HTTP endpoint. This subclass preserves Genblaze's provider and
Pipeline contracts while using the current hosted transport documented on
build.nvidia.com.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx
from genblaze_core._utils import local_file_url
from genblaze_core.exceptions import ProviderError
from genblaze_core.models.asset import Asset, AudioMetadata
from genblaze_core.models.enums import ProviderErrorCode
from genblaze_core.models.step import Step
from genblaze_core.providers import LiveProbeResult
from genblaze_core.runnable.config import RunnableConfig
from genblaze_nvidia import NvidiaAudioProvider


DEFAULT_MAGPIE_SYNTHESIZE_URL = (
    "https://877104f7-e885-42b9-8de8-f6e4c6303969.invocation.api.nvcf.nvidia.com"
    "/v1/audio/synthesize"
)
DEFAULT_MAGPIE_VOICES_URL = (
    "https://877104f7-e885-42b9-8de8-f6e4c6303969.invocation.api.nvcf.nvidia.com"
    "/v1/audio/list_voices"
)
MAGPIE_MODEL = "nvidia/magpie-tts-multilingual"


class NvidiaHostedMagpieAudioProvider(NvidiaAudioProvider):
    """Run Magpie TTS through NVIDIA's hosted Riva HTTP endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        output_dir: Path | str,
        synthesize_url: str = DEFAULT_MAGPIE_SYNTHESIZE_URL,
        voices_url: str = DEFAULT_MAGPIE_VOICES_URL,
        http_timeout: float = 120.0,
        hosted_http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key=api_key, output_dir=output_dir, http_timeout=http_timeout)
        self._hosted_output_dir = Path(output_dir)
        self._synthesize_url = synthesize_url
        self._voices_url = voices_url
        self._owns_hosted_client = hosted_http_client is None
        self._hosted_http = hosted_http_client or httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=http_timeout,
        )

    def _invoke_family_probe(self, probe, model_id: str) -> LiveProbeResult:
        if model_id != MAGPIE_MODEL:
            return super()._invoke_family_probe(probe, model_id)
        try:
            response = self._hosted_http.get(self._voices_url)
        except httpx.HTTPError:
            return LiveProbeResult.UNKNOWN
        if response.status_code == 200:
            return LiveProbeResult.LIVE
        if response.status_code == 404:
            return LiveProbeResult.DEAD
        return LiveProbeResult.UNKNOWN

    def generate(self, step: Step, config: RunnableConfig | None = None) -> Step:
        if step.model != MAGPIE_MODEL:
            return super().generate(step, config)
        if not step.prompt or not step.prompt.strip():
            raise ProviderError(
                "NVIDIA Magpie TTS requires narration text",
                error_code=ProviderErrorCode.INVALID_INPUT,
            )

        language = str(step.params.get("language", "en-US"))
        voice = str(step.params.get("voice", "Magpie-Multilingual.EN-US.Aria"))
        encoding = str(step.params.get("encoding", "LINEAR_PCM"))
        sample_rate_hz = int(step.params.get("sample_rate_hz", 44100))
        try:
            response = self._hosted_http.post(
                self._synthesize_url,
                data={
                    "text": step.prompt,
                    "language": language,
                    "voice": voice,
                    "encoding": encoding,
                    "sample_rate_hz": str(sample_rate_hz),
                },
            )
        except httpx.HTTPError as exc:
            raise ProviderError(
                "NVIDIA Magpie TTS request failed before completion",
                error_code=ProviderErrorCode.SERVER_ERROR,
            ) from exc
        if response.status_code != 200:
            raise ProviderError(
                f"NVIDIA Magpie TTS failed with HTTP {response.status_code}",
                error_code=(
                    ProviderErrorCode.AUTH_FAILURE
                    if response.status_code in {401, 403}
                    else ProviderErrorCode.SERVER_ERROR
                ),
            )
        if not response.content:
            raise ProviderError(
                "NVIDIA Magpie TTS returned an empty audio file",
                error_code=ProviderErrorCode.SERVER_ERROR,
            )

        self._hosted_output_dir.mkdir(parents=True, exist_ok=True)
        path = self._hosted_output_dir / f"nvidia-magpie-{uuid.uuid4().hex[:12]}.wav"
        path.write_bytes(response.content)
        asset = Asset(url=local_file_url(path.resolve()), media_type="audio/wav")
        asset.audio = AudioMetadata(channels=1, codec="pcm", sample_rate=sample_rate_hz)
        step.assets.append(asset)
        step.provider_payload = {
            "nvidia": {"status": "succeeded", "transport": "hosted-riva-http"}
        }
        return step

    def close(self) -> None:
        if self._owns_hosted_client:
            self._hosted_http.close()
        super().close()
