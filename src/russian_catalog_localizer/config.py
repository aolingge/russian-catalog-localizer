from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    source_dir: Path
    work_dir: Path
    output_dir: Path
    glossary: Path
    render_dpi: int = 240
    target_language: str = "ru"
    max_package_file_mb: float = 50.0

    @classmethod
    def from_toml(cls, path: Path) -> PipelineConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        paths = data.get("paths", {})
        ocr = data.get("ocr", {})
        translation = data.get("translation", {})
        qa = data.get("qa", {})
        base = path.parent
        return cls(
            source_dir=(base / paths.get("source_dir", "data/source")).resolve(),
            work_dir=(base / paths.get("work_dir", "work")).resolve(),
            output_dir=(base / paths.get("output_dir", "output")).resolve(),
            glossary=(base / paths.get("glossary", "examples/glossary.zh-ru.csv")).resolve(),
            render_dpi=int(ocr.get("render_dpi", 240)),
            target_language=str(translation.get("target_language", "ru")),
            max_package_file_mb=float(qa.get("max_package_file_mb", 50)),
        )
