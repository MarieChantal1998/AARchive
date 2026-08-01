import json
from datetime import datetime
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .keys import frame_key, metadata_key, source_key
from .models import Correction, Project, Scene
from .seed import DEMO_SCENES, demo_project
from .settings import Settings


class StorageUnavailable(RuntimeError):
    pass


class B2Store:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def configured(self) -> bool:
        return self.settings.b2_configured

    @property
    def client(self):
        if not self.configured:
            raise StorageUnavailable("Backblaze B2 credentials are not configured")
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.b2_endpoint_url,
                region_name=self.settings.b2_region,
                aws_access_key_id=self.settings.b2_key_id,
                aws_secret_access_key=self.settings.b2_app_key,
                config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
            )
        return self._client

    def put_json(self, key: str, value: Any) -> None:
        payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        self.client.put_object(
            Bucket=self.settings.b2_bucket,
            Key=key,
            Body=json.dumps(payload, separators=(",", ":"), default=_json_default).encode(),
            ContentType="application/json",
        )

    def put_bytes(self, key: str, payload: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.settings.b2_bucket,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.settings.b2_bucket, Key=key)
            return True
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise StorageUnavailable(f"Could not verify B2 object {key}") from exc

    def connected(self) -> bool:
        if not self.configured:
            return False
        try:
            self.client.head_bucket(Bucket=self.settings.b2_bucket)
            return True
        except (ClientError, BotoCoreError):
            return False

    def get_json(self, key: str) -> Any:
        try:
            response = self.client.get_object(Bucket=self.settings.b2_bucket, Key=key)
            return json.loads(response["Body"].read())
        except (ClientError, BotoCoreError, json.JSONDecodeError) as exc:
            raise StorageUnavailable(f"Could not read B2 object {key}") from exc

    def list_projects(self) -> list[Project]:
        projects = [demo_project(self.settings.demo_video_url)]
        if not self.configured:
            return projects
        paginator = self.client.get_paginator("list_objects_v2")
        try:
            for page in paginator.paginate(Bucket=self.settings.b2_bucket, Prefix="projects/"):
                for item in page.get("Contents", []):
                    key = item["Key"]
                    if key.endswith("/metadata/project.json"):
                        project = Project.model_validate(self.get_json(key))
                        if project.project_id != projects[0].project_id:
                            projects.append(project)
        except (ClientError, BotoCoreError, StorageUnavailable):
            return projects
        return sorted(projects, key=lambda project: project.created_at, reverse=True)

    def with_download_urls(self, project: Project) -> Project:
        hydrated = project.model_copy(deep=True)
        if hydrated.seeded_demo:
            return hydrated
        if self.exists(source_key(project.project_id)):
            hydrated.video_url = self.presign_download(source_key(project.project_id))
        if hydrated.indexed_scene_count and self.exists(frame_key(project.project_id, 1)):
            hydrated.thumbnail_url = self.presign_download(frame_key(project.project_id, 1))
        return hydrated

    def list_keys(self, prefix: str = "projects/") -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.settings.b2_bucket, Prefix=prefix):
            output.extend({"key": item["Key"], "size": item["Size"]} for item in page.get("Contents", []))
        return output

    def get_project(self, project_id: str) -> Project:
        if project_id == "demo-coordinated-response":
            return demo_project(self.settings.demo_video_url)
        return Project.model_validate(self.get_json(metadata_key(project_id, "project")))

    def get_scenes(self, project_id: str) -> list[Scene]:
        if project_id == "demo-coordinated-response":
            return [scene.model_copy(deep=True) for scene in DEMO_SCENES]
        return [Scene.model_validate(item) for item in self.get_json(metadata_key(project_id, "scenes"))]

    def get_corrections(self, project_id: str) -> list[Correction]:
        if project_id == "demo-coordinated-response" or not self.configured:
            return []
        try:
            return [Correction.model_validate(item) for item in self.get_json(metadata_key(project_id, "corrections"))]
        except StorageUnavailable:
            return []

    def presign_upload(self, key: str, content_type: str, expires: int = 900) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.settings.b2_bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def presign_download(self, key: str, expires: int = 3600) -> str:
        if self.settings.b2_public_url_base:
            return f"{self.settings.b2_public_url_base.rstrip('/')}/{key}"
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.settings.b2_bucket, "Key": key}, ExpiresIn=expires
        )


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
