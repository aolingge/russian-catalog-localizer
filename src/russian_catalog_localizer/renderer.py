from __future__ import annotations

import json
from pathlib import Path

from .models import Segment


def build_repaint_plan(segments: list[Segment]) -> dict[str, object]:
    layers = []
    for segment in segments:
        layers.append(
            {
                "page": segment.page,
                "bbox": segment.bbox.to_list(),
                "source_text": segment.text,
                "target_text": segment.translated_text or segment.text,
                "strategy": "overlay-text",
                "notes": segment.notes,
            }
        )
    return {
        "schema_version": 1,
        "description": "Renderer-neutral repaint plan for localized catalog text.",
        "layers": layers,
    }


def write_repaint_plan(path: Path, segments: list[Segment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_repaint_plan(segments)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
