from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from russian_catalog_localizer.glossary import GlossaryEntry, localize_segments
from russian_catalog_localizer.models import Box, Segment
from russian_catalog_localizer.packager import pack_directory
from russian_catalog_localizer.qa import residual_cjk_hits


class PipelineTests(unittest.TestCase):
    def test_glossary_localizes_known_terms(self) -> None:
        segments = [Segment(page=1, text="额定电压", bbox=Box(0, 0, 10, 10))]
        glossary = [GlossaryEntry(source="额定电压", target="Номинальное напряжение")]

        localized = localize_segments(segments, glossary)

        self.assertEqual(localized[0].translated_text, "Номинальное напряжение")
        self.assertEqual(residual_cjk_hits(localized), [])

    def test_unknown_cjk_is_flagged(self) -> None:
        segments = [Segment(page=1, text="未知术语", bbox=Box(0, 0, 10, 10))]

        localized = localize_segments(segments, [])

        self.assertIn("todo:needs-translation", localized[0].notes)
        self.assertEqual(len(residual_cjk_hits(localized)), 1)

    def test_packager_skips_private_generated_and_large_files(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "safe.txt").write_text("publishable\n", encoding="utf-8")
            (source / ".env").write_text("API_KEY=do-not-package\n", encoding="utf-8")
            (source / "large.bin").write_bytes(b"x" * 2048)
            cache = source / "__pycache__"
            cache.mkdir()
            (cache / "module.pyc").write_bytes(b"bytecode")

            zip_path = Path(tmp) / "release.zip"
            added = pack_directory(source, zip_path, max_file_mb=0.001)

            self.assertEqual(added, ["safe.txt"])
            with ZipFile(zip_path) as archive:
                self.assertEqual(archive.namelist(), ["safe.txt"])


if __name__ == "__main__":
    unittest.main()
