from __future__ import annotations

import fnmatch
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

EXCLUDE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "Thumbs.db",
}

EXCLUDE_PATTERNS = [
    ".env*",
    "*.csv",
    "*.db",
    "*.json",
    "*.key",
    "*.log",
    "*.pem",
    "*.pfx",
    "*.p12",
    "*.pyc",
    "*.pdf",
    "*.sqlite",
    "*.sqlite3",
    "*.toml",
    "*.zip",
    "*.7z",
    "*.rar",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.tif",
    "*.tiff",
    "data/*",
    "work/*",
    "output/*",
    "release/*",
    ".cache/*",
    "cache/*",
    "*cookie*",
    "*credentials*",
    "*service-account*",
    "*secret*",
    "*token*",
    "__pycache__/*",
]


def is_private_or_generated(path: Path, relative_name: str, max_bytes: int) -> bool:
    if path.name in EXCLUDE_NAMES:
        return True
    if path.stat().st_size > max_bytes:
        return True
    normalized = relative_name.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in EXCLUDE_PATTERNS)


def pack_directory(
    source_dir: Path,
    zip_path: Path,
    *,
    max_file_mb: float = 50.0,
    allowed_names: set[str] | tuple[str, ...] | None = None,
) -> list[str]:
    source_dir = source_dir.resolve()
    zip_path = zip_path.resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    max_bytes = int(max_file_mb * 1024 * 1024)
    allowed = set(allowed_names or ())
    added: list[str] = []

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.resolve() == zip_path:
                continue
            relative_name = path.relative_to(source_dir).as_posix()
            if allowed:
                if relative_name not in allowed or path.stat().st_size > max_bytes:
                    continue
            elif is_private_or_generated(path, relative_name, max_bytes):
                continue
            archive.write(path, relative_name)
            added.append(relative_name)
    return added
