from __future__ import annotations

import unittest
from importlib.resources import as_file, files
from pathlib import Path
from tempfile import TemporaryDirectory

from russian_catalog_localizer.desktop_app import (
    build_qa_summary,
    build_result_message,
    default_output_dir,
    demo_resource_paths,
    run_desktop_workflow,
    validate_workflow_inputs,
)


class DesktopAppTests(unittest.TestCase):
    def test_run_desktop_workflow_writes_outputs_and_summary(self) -> None:
        with TemporaryDirectory() as tmp, demo_resource_paths() as (
            segments_path,
            glossary_path,
        ):
            result = run_desktop_workflow(segments_path, glossary_path, Path(tmp))

            self.assertTrue(result.segments_path.is_file())
            self.assertTrue(result.repaint_plan_path.is_file())
            self.assertTrue(result.qa_report_path.is_file())
            self.assertTrue(result.package_path.is_file())
            self.assertEqual(result.segment_count, 7)
            self.assertEqual(result.residual_cjk_count, 0)
            self.assertIn("QA 摘要", result.qa_summary)
            self.assertIn("残留中文: 0", result.qa_summary)
            message = build_result_message(result)
            self.assertIn("脱敏分享包", message)
            self.assertIn("下一步", message)

    def test_build_qa_summary_uses_report_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            qa_path = Path(tmp) / "qa_report.md"
            package_path = Path(tmp) / "localized_package.zip"
            qa_path.write_text(
                "\n".join(
                    [
                        "# Localization QA Report",
                        "",
                        "- Segments checked: 2",
                        "- Residual Chinese hits: 1",
                        "",
                        "## Residual Chinese",
                        "",
                        "### Page 1",
                        "- `未知术语` at `[0.0, 0.0, 1.0, 1.0]`",
                    ]
                ),
                encoding="utf-8",
            )

            summary = build_qa_summary(
                segment_count=2,
                residual_cjk_count=1,
                qa_report_path=qa_path,
                package_path=package_path,
                packaged_files=("segments.ru.json",),
            )

            self.assertIn("Residual Chinese hits: 1", summary)
            self.assertIn("### Page 1", summary)
            self.assertIn("未知术语", summary)

    def test_demo_resource_paths_match_packaged_examples(self) -> None:
        example_dir = files("russian_catalog_localizer").joinpath("examples")
        with (
            demo_resource_paths() as (segments_path, glossary_path),
            as_file(example_dir.joinpath("sample_ocr_segments.json")) as expected_segments,
        ):
            actual = segments_path.read_text(encoding="utf-8")
            expected = expected_segments.read_text(encoding="utf-8")

            self.assertEqual(actual, expected)
            self.assertTrue(glossary_path.name.endswith(".csv"))

    def test_validate_workflow_inputs_returns_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            segments = root / "segments.json"
            glossary = root / "glossary.csv"
            out_dir = root / "out"
            segments.write_text('{"segments":[]}\n', encoding="utf-8")
            glossary.write_text("source,target\n", encoding="utf-8")

            result = validate_workflow_inputs(str(segments), str(glossary), str(out_dir))

            self.assertEqual(result.segments_path, segments)
            self.assertEqual(result.glossary_path, glossary)
            self.assertEqual(result.output_dir, out_dir)

    def test_validate_workflow_inputs_reports_actionable_errors(self) -> None:
        with self.assertRaises(ValueError) as context:
            validate_workflow_inputs("", "", "")

        message = str(context.exception)
        self.assertIn("请选择 OCR JSON 文件", message)
        self.assertIn("请选择术语表 CSV 文件", message)
        self.assertIn("请选择输出目录", message)

    def test_default_output_dir_is_customer_named(self) -> None:
        self.assertIn("俄文目录", str(default_output_dir()))


if __name__ == "__main__":
    unittest.main()
