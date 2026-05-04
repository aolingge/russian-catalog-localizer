from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import Segment

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_segments(path: Path) -> list[Segment]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    raw_segments = payload["segments"] if isinstance(payload, dict) else payload
    return [Segment.from_dict(item) for item in raw_segments]


def normalize_segments(segments: list[Segment]) -> list[Segment]:
    for segment in segments:
        segment.text = normalize_text(segment.text)
    return segments


def write_segments(path: Path, segments: list[Segment], *, source: str = "localizer") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "source": source,
        "segments": [segment.to_dict() for segment in segments],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
