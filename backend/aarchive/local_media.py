"""Zero-cost local media providers for the cached hackathon demonstration."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import textwrap
import uuid
from pathlib import Path

from genblaze_core._utils import local_file_url
from genblaze_core.exceptions import ProviderError
from genblaze_core.models.asset import Asset, AudioMetadata
from genblaze_core.models.enums import Modality, ProviderErrorCode
from genblaze_core.models.step import Step
from genblaze_core.providers.base import ProviderCapabilities, SyncProvider
from genblaze_core.runnable.config import RunnableConfig
from PIL import Image, ImageDraw, ImageFont

LOCAL_IMAGE_MODEL = "pillow-lesson-card-v1"
LOCAL_AUDIO_MODEL = "macos-say-tts-v1"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


def _prompt_value(prompt: str, label: str, stop_label: str | None = None) -> str:
    stop = rf"(?=\s+{re.escape(stop_label)}:)" if stop_label else "$"
    match = re.search(rf"{re.escape(label)}:\s*(.+?){stop}", prompt, flags=re.IGNORECASE)
    return match.group(1).strip().rstrip(".") if match else ""


class LocalLessonCardProvider(SyncProvider):
    """Render a deterministic, prompt-derived after-action lesson card."""

    name = "local-lesson-card"

    def __init__(self, *, output_dir: Path | str) -> None:
        super().__init__()
        self.output_dir = Path(output_dir)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supported_modalities=[Modality.IMAGE],
            supported_inputs=["text"],
            models=[LOCAL_IMAGE_MODEL],
            output_formats=["image/png"],
        )

    def generate(self, step: Step, config: RunnableConfig | None = None) -> Step:
        width = int(step.params.get("width", 1536))
        height = int(step.params.get("height", 864))
        if width < 640 or height < 360:
            raise ProviderError(
                "Local lesson card dimensions are too small",
                error_code=ProviderErrorCode.INVALID_INPUT,
            )
        prompt = step.prompt or "After-action training brief"
        title = _prompt_value(prompt, "Theme", "Training topics") or "After-Action Training Brief"
        topics = _prompt_value(prompt, "Training topics") or "coordination, communication, recovery"
        topic_labels = [item.strip().title() for item in topics.split(",") if item.strip()][:4]
        seed = hashlib.sha256(prompt.encode("utf-8")).digest()

        image = Image.new("RGB", (width, height), "#111418")
        draw = ImageDraw.Draw(image)
        for y in range(height):
            blend = y / max(1, height - 1)
            color = (
                int(17 + 8 * blend),
                int(20 + 9 * blend),
                int(24 + 12 * blend),
            )
            draw.line((0, y, width, y), fill=color)

        amber = "#F1A84B"
        pale = "#F4F0E8"
        muted = "#A6ADB5"
        panel = "#1B2026"
        draw.rectangle((0, 0, 22, height), fill=amber)
        draw.rounded_rectangle((90, 80, width - 90, height - 80), radius=28, fill=panel)
        draw.rectangle((90, 80, width - 90, 88), fill=amber)

        kicker_font = _font(24, bold=True)
        title_font = _font(64, bold=True)
        body_font = _font(27)
        tag_font = _font(22, bold=True)
        small_font = _font(20)
        draw.text((145, 140), "AARCHIVE  /  GENERATED LESSON CARD", font=kicker_font, fill=amber)

        wrapped_title = textwrap.wrap(title, width=35)[:3]
        y = 215
        for line in wrapped_title:
            draw.text((145, y), line, font=title_font, fill=pale)
            y += 76

        draw.text(
            (145, y + 12),
            "Selected footage → searchable evidence → facilitated review",
            font=body_font,
            fill=muted,
        )

        tag_y = y + 92
        tag_x = 145
        for index, topic in enumerate(topic_labels or ["Training Review"]):
            label = topic[:28]
            box_width = int(draw.textlength(label, font=tag_font)) + 42
            if tag_x + box_width > width - 145:
                tag_x = 145
                tag_y += 58
            draw.rounded_rectangle(
                (tag_x, tag_y, tag_x + box_width, tag_y + 42),
                radius=18,
                outline=amber if index == 0 else "#59616B",
                width=2,
                fill="#242A31",
            )
            draw.text((tag_x + 21, tag_y + 8), label, font=tag_font, fill=pale)
            tag_x += box_width + 16

        timeline_y = height - 220
        draw.line((145, timeline_y, width - 145, timeline_y), fill="#56606A", width=4)
        for index in range(5):
            x = 145 + index * ((width - 290) // 4)
            radius = 12 + seed[index] % 5
            draw.ellipse((x - radius, timeline_y - radius, x + radius, timeline_y + radius), fill=amber)
            if index < 4:
                lift = 28 + seed[index + 5] % 45
                draw.line((x, timeline_y, x + 95, timeline_y - lift), fill="#7B8793", width=3)

        draw.text(
            (145, height - 145),
            "MACHINE-GENERATED MEDIA  •  HUMAN REVIEW REQUIRED  •  PUBLIC / SYNTHETIC FOOTAGE ONLY",
            font=small_font,
            fill=muted,
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"aarchive-lesson-card-{uuid.uuid4().hex[:12]}.png"
        image.save(path, format="PNG", optimize=True)
        step.assets.append(Asset(url=local_file_url(path.resolve()), media_type="image/png"))
        step.provider_payload = {
            "local": {
                "status": "succeeded",
                "renderer": "Pillow",
                "algorithm": LOCAL_IMAGE_MODEL,
            }
        }
        step.cost_usd = 0
        return step


class LocalNarrationProvider(SyncProvider):
    """Generate offline narration with macOS Say and encode it with FFmpeg."""

    name = "local-narration"

    def __init__(self, *, output_dir: Path | str) -> None:
        super().__init__()
        self.output_dir = Path(output_dir)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supported_modalities=[Modality.AUDIO],
            supported_inputs=["text"],
            models=[LOCAL_AUDIO_MODEL],
            output_formats=["audio/mpeg"],
        )

    def generate(self, step: Step, config: RunnableConfig | None = None) -> Step:
        narration = (step.prompt or "").strip()
        if not narration:
            raise ProviderError(
                "Local narration requires text",
                error_code=ProviderErrorCode.INVALID_INPUT,
            )
        say = shutil.which("say")
        ffmpeg = shutil.which("ffmpeg")
        if not say or not ffmpeg:
            raise ProviderError(
                "Local narration requires macOS Say and FFmpeg",
                error_code=ProviderErrorCode.NOT_FOUND,
            )

        voice = str(step.params.get("voice", "Samantha"))
        rate = int(step.params.get("rate", 155))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"aarchive-narration-{uuid.uuid4().hex[:12]}"
        aiff_path = self.output_dir / f"{stem}.aiff"
        mp3_path = self.output_dir / f"{stem}.mp3"
        try:
            subprocess.run(
                [say, "-v", voice, "-r", str(rate), "-o", str(aiff_path), narration],
                check=True,
                capture_output=True,
                timeout=180,
            )
            subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(aiff_path),
                    "-codec:a",
                    "libmp3lame",
                    "-b:a",
                    "128k",
                    str(mp3_path),
                ],
                check=True,
                capture_output=True,
                timeout=180,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ProviderError(
                "Offline narration did not complete",
                error_code=ProviderErrorCode.SERVER_ERROR,
            ) from exc
        finally:
            aiff_path.unlink(missing_ok=True)

        asset = Asset(url=local_file_url(mp3_path.resolve()), media_type="audio/mpeg")
        asset.audio = AudioMetadata(channels=1, codec="mp3")
        step.assets.append(asset)
        step.provider_payload = {
            "local": {
                "status": "succeeded",
                "engine": "macOS Say",
                "encoder": "FFmpeg/libmp3lame",
                "voice": voice,
                "rate": rate,
            }
        }
        step.cost_usd = 0
        return step
