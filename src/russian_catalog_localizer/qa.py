from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import Segment
from .ocr import has_cjk


def residual_cjk_hits(segments: list[Segment]) -> list[Segment]:
    return [segment for segment in segments if has_cjk(segment.translated_text or segment.text)]


def build_report(segments: list[Segment]) -> str:
    hits = residual_cjk_hits(segments)
    by_page: dict[int, list[Segment]] = defaultdict(list)
    for hit in hits:
        by_page[hit.page].append(hit)

    lines = [
        "# Localization QA Report",
        "",
        f"- Segments checked: {len(segments)}",
        f"- Residual Chinese hits: {len(hits)}",
        "",
    ]

    if not hits:
        lines.append("No residual CJK text was found in localized segment text.")
    else:
        lines.extend(["## Residual Chinese", ""])
        for page in sorted(by_page):
            lines.append(f"### Page {page}")
            for segment in by_page[page]:
                target = segment.translated_text or segment.text
                lines.append(f"- `{target}` at `{segment.bbox.to_list()}`")
            lines.append("")

    lines.extend(
        [
            "",
            "## Manual Visual QA",
            "",
            "- Build contact sheets from final page renders.",
            "- Check table headers, dense labels, and Cyrillic font coverage.",
            "- Re-run OCR residual detection on the final PDF when a renderer is attached.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: Path, segments: list[Segment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_report(segments), encoding="utf-8")
