from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path

from .models import Segment
from .ocr import has_cjk


@dataclass(frozen=True)
class GlossaryEntry:
    source: str
    target: str
    note: str = ""


def load_glossary(path: Path) -> list[GlossaryEntry]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        entries = []
        for row in reader:
            source = (row.get("source") or "").strip()
            target = (row.get("target") or "").strip()
            if not source or not target:
                continue
            entries.append(GlossaryEntry(source=source, target=target, note=(row.get("note") or "")))
    return entries


def apply_glossary(text: str, entries: list[GlossaryEntry]) -> tuple[str, list[str]]:
    exact = {entry.source: entry.target for entry in entries}
    if text in exact:
        return exact[text], [f"exact:{text}"]

    translated = text
    matches: list[str] = []
    for entry in sorted(entries, key=lambda item: len(item.source), reverse=True):
        if entry.source in translated:
            translated = translated.replace(entry.source, entry.target)
            matches.append(f"term:{entry.source}")
    return translated, matches


def localize_segments(segments: list[Segment], entries: list[GlossaryEntry]) -> list[Segment]:
    localized: list[Segment] = []
    for segment in segments:
        translated, matches = apply_glossary(segment.text, entries)
        notes = [*segment.notes, *matches]
        if translated == segment.text and has_cjk(translated):
            notes.append("todo:needs-translation")
        localized.append(replace(segment, translated_text=translated, notes=notes))
    return localized
