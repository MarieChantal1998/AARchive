import pytest

from aarchive.genblaze_service import GenerationUnavailable, GenblazeBriefService
from aarchive.generation_providers import provider_for
from aarchive.models import BriefRequest
from aarchive.seed import DEMO_SCENES
from aarchive.settings import Settings


def test_service_reports_missing_credentials_without_faking_success():
    service = GenblazeBriefService(Settings())
    assert service.available is False
    with pytest.raises(GenerationUnavailable):
        service.generate(
            BriefRequest(project_id="demo", scene_ids=["scene-001"]),
            "Demo",
            DEMO_SCENES[:1],
        )


def test_service_source_uses_real_genblaze_api():
    import inspect

    source = inspect.getsource(GenblazeBriefService)
    assert 'from genblaze_core import Modality, Pipeline' in source
    assert "ObjectStorageSink" in source
    assert "S3StorageBackend.for_backblaze" in source
    providers = inspect.getsource(provider_for)
    assert "GMICloudImageProvider" in providers
    assert "GMICloudAudioProvider" in providers
    assert "NvidiaImageProvider" in providers
    assert "NvidiaAudioProvider" in providers
    assert "DalleProvider" in providers
    assert "OpenAITTSProvider" in providers


def test_brief_id_is_stable_for_cached_generation():
    first = BriefRequest(project_id="project", scene_ids=["scene-002", "scene-001"])
    second = BriefRequest(project_id="project", scene_ids=["scene-001", "scene-002"])
    assert GenblazeBriefService.brief_id_for(first) == GenblazeBriefService.brief_id_for(second)
