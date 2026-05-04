from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .glossary import load_glossary, localize_segments
from .models import Segment
from .ocr import load_segments, normalize_segments, write_segments
from .packager import pack_directory
from .qa import residual_cjk_hits, write_report
from .renderer import write_repaint_plan


@dataclass(frozen=True)
class WorkflowResult:
    output_dir: Path
    localized_segments: Path
    repaint_plan: Path
    qa_report: Path
    package_zip: Path
    segment_count: int
    residual_chinese_count: int
    packaged_files: tuple[str, ...]


SAFE_PACKAGE_FILES = ("segments.ru.json", "repaint_plan.json", "qa_report.md")
SOURCE_NOTE_PREFIXES = ("exact:", "term:")


def public_note(note: str) -> str:
    if note.startswith(SOURCE_NOTE_PREFIXES):
        return "glossary-match"
    return note


def public_target_text(segment: Segment) -> str:
    target = segment.translated_text or ""
    if residual_cjk_hits([segment]):
        return "[redacted: residual CJK text]"
    return target


def public_segment_dict(segment: Segment) -> dict[str, object]:
    notes = sorted({public_note(note) for note in segment.notes})
    data: dict[str, object] = {
        "page": segment.page,
        "bbox": segment.bbox.to_list(),
        "translated_text": public_target_text(segment),
    }
    if notes:
        data["notes"] = notes
    return data


def build_public_segments_payload(segments: list[Segment]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source": "localized-public-sanitized",
        "privacy": "Source OCR text and glossary source terms are removed from this package.",
        "segments": [public_segment_dict(segment) for segment in segments],
    }


def build_public_repaint_plan(segments: list[Segment]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "description": "Sanitized repaint plan for downstream localized text placement.",
        "privacy": "Source OCR text is intentionally omitted.",
        "layers": [
            {
                "page": segment.page,
                "bbox": segment.bbox.to_list(),
                "target_text": public_target_text(segment),
                "strategy": "overlay-text",
                "notes": sorted({public_note(note) for note in segment.notes}),
            }
            for segment in segments
        ],
    }


def build_public_qa_report(segments: list[Segment]) -> str:
    hits = residual_cjk_hits(segments)
    page_counts = Counter(segment.page for segment in hits)
    lines = [
        "# Localization QA Public Summary",
        "",
        f"- Segments checked: {len(segments)}",
        f"- Residual Chinese hits: {len(hits)}",
        "- Privacy: residual text is redacted from this public package.",
        "",
    ]
    if page_counts:
        lines.extend(["## Pages Requiring Review", ""])
        for page, count in sorted(page_counts.items()):
            lines.append(f"- Page {page}: {count} residual segment(s)")
    else:
        lines.append("No residual CJK text was found in localized segment text.")
    return "\n".join(lines).rstrip() + "\n"


def write_safe_package_artifacts(path: Path, segments: list[Segment]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "segments.ru.json").write_text(
        json.dumps(build_public_segments_payload(segments), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (path / "repaint_plan.json").write_text(
        json.dumps(build_public_repaint_plan(segments), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (path / "qa_report.md").write_text(build_public_qa_report(segments), encoding="utf-8")


def run_localization_workflow(
    segments_path: Path,
    glossary_path: Path,
    out_dir: Path,
) -> WorkflowResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    segments = normalize_segments(load_segments(segments_path))
    glossary = load_glossary(glossary_path)
    localized = localize_segments(segments, glossary)

    localized_path = out_dir / "segments.ru.json"
    repaint_path = out_dir / "repaint_plan.json"
    qa_path = out_dir / "qa_report.md"
    package_path = out_dir / "localized_package.zip"

    write_segments(localized_path, localized, source="localized")
    write_repaint_plan(repaint_path, localized)
    write_report(qa_path, localized)
    with TemporaryDirectory(prefix="rcl-safe-package-") as tmp:
        safe_dir = Path(tmp)
        write_safe_package_artifacts(safe_dir, localized)
        added = pack_directory(safe_dir, package_path, allowed_names=SAFE_PACKAGE_FILES)

    return WorkflowResult(
        output_dir=out_dir,
        localized_segments=localized_path,
        repaint_plan=repaint_path,
        qa_report=qa_path,
        package_zip=package_path,
        segment_count=len(localized),
        residual_chinese_count=len(residual_cjk_hits(localized)),
        packaged_files=tuple(added),
    )
