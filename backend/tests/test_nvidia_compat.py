from pathlib import Path

import httpx
from genblaze_core.models.enums import Modality
from genblaze_core.models.step import Step
from genblaze_core.providers import LiveProbeResult

from aarchive.nvidia_compat import MAGPIE_MODEL, NvidiaHostedMagpieAudioProvider


def test_hosted_magpie_probe_and_generation_use_current_http_contract(tmp_path):
    requests: list[tuple[str, str, bytes]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        requests.append((request.method, str(request.url), body))
        if request.method == "GET":
            return httpx.Response(200, json={"en-US": {"voices": ["Aria"]}})
        return httpx.Response(200, content=b"RIFF-test-audio", headers={"content-type": "audio/wav"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = NvidiaHostedMagpieAudioProvider(
        "server-only-test-key",
        output_dir=tmp_path,
        synthesize_url="https://example.test/v1/audio/synthesize",
        voices_url="https://example.test/v1/audio/list_voices",
        hosted_http_client=client,
    )
    assert provider._invoke_family_probe(None, MAGPIE_MODEL) == LiveProbeResult.LIVE

    step = Step(
        provider=provider.name,
        model=MAGPIE_MODEL,
        prompt="A short verified after-action narration.",
        modality=Modality.AUDIO,
        params={"voice": "Magpie-Multilingual.EN-US.Aria"},
    )
    completed = provider.generate(step)
    assert len(completed.assets) == 1
    assert completed.assets[0].media_type == "audio/wav"
    assert Path(completed.assets[0].url.removeprefix("file://")).read_bytes() == b"RIFF-test-audio"
    assert requests[0][0] == "GET"
    assert requests[1][0] == "POST"
    assert b"A+short+verified+after-action+narration" in requests[1][2]
    assert b"server-only-test-key" not in requests[1][2]
    provider.close()
