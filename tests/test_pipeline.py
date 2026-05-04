from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from russian_catalog_localizer.glossary import GlossaryEntry, localize_segments
from russian_catalog_localizer.models import Box, Segment
from russian_catalog_localizer.packager import pack_directory
from russian_catalog_localizer.qa import residual_cjk_hits
from russian_catalog_localizer.workflow import run_localization_workflow


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
            (source / ".env.staging").write_text("API_KEY=do-not-package\n", encoding="utf-8")
            (source / "customer.pdf").write_bytes(b"%PDF-private")
            (source / "customer.json").write_text('{"text":"private"}\n', encoding="utf-8")
            (source / "glossary.csv").write_text("source,target\n秘密,secret\n", encoding="utf-8")
            (source / "token.json").write_text('{"token":"secret"}\n', encoding="utf-8")
            (source / "debug.log").write_text("private log\n", encoding="utf-8")
            (source / "page.png").write_bytes(b"private-image")
            (source / "large.bin").write_bytes(b"x" * 2048)
            cache_dir = source / ".cache"
            cache_dir.mkdir()
            (cache_dir / "state.txt").write_text("private cache\n", encoding="utf-8")
            cache = source / "__pycache__"
            cache.mkdir()
            (cache / "module.pyc").write_bytes(b"bytecode")

            zip_path = Path(tmp) / "release.zip"
            added = pack_directory(source, zip_path, max_file_mb=0.001)

            self.assertEqual(added, ["safe.txt"])
            with ZipFile(zip_path) as archive:
                self.assertEqual(archive.namelist(), ["safe.txt"])

    def test_workflow_writes_expected_customer_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            segments_path = root / "segments.json"
            glossary_path = root / "glossary.csv"
            out_dir = root / "out"
            segments_path.write_text(
                """
{
  "segments": [
    {"page": 1, "text": "额定电压", "bbox": [0, 0, 10, 10]},
    {"page": 1, "text": "未知术语", "bbox": [0, 12, 10, 22]}
  ]
}
""".strip(),
                encoding="utf-8",
            )
            glossary_path.write_text(
                "source,target,note\n额定电压,Номинальное напряжение,\n",
                encoding="utf-8",
            )

            result = run_localization_workflow(segments_path, glossary_path, out_dir)

            self.assertEqual(result.segment_count, 2)
            self.assertEqual(result.residual_chinese_count, 1)
            self.assertTrue(result.localized_segments.exists())
            self.assertTrue(result.repaint_plan.exists())
            self.assertTrue(result.qa_report.exists())
            self.assertTrue(result.package_zip.exists())
            with ZipFile(result.package_zip) as archive:
                self.assertEqual(
                    archive.namelist(),
                    ["qa_report.md", "repaint_plan.json", "segments.ru.json"],
                )
                packaged_text = "\n".join(
                    archive.read(name).decode("utf-8") for name in archive.namelist()
                )
            self.assertNotIn("额定电压", packaged_text)
            self.assertNotIn("未知术语", packaged_text)
            self.assertNotIn("source_text", packaged_text)
            self.assertNotIn("exact:", packaged_text)
            self.assertNotIn("term:", packaged_text)
            self.assertIn("Номинальное напряжение", packaged_text)
            self.assertIn("[redacted: residual CJK text]", packaged_text)


if __name__ == "__main__":
    unittest.main()
