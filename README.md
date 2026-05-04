# Russian Catalog Localizer

Open-source skeleton for localizing Chinese product catalogs into Russian without committing private source PDFs, customer data, API keys, or large binary artifacts.

The pipeline shape is:

1. OCR Chinese PDF or page images into text segments with bounding boxes.
2. Apply a Chinese to Russian glossary before any machine translation.
3. Produce a repaint plan for overlay rendering or local patching.
4. Run QA for residual Chinese text and visual contact-sheet review.
5. Package only the safe release artifacts.

This repository includes a tiny synthetic sample. It does not include the original catalog PDF or proprietary translation tables.

## Quick Start

Run from a source checkout:

```powershell
cd russian-catalog-localizer
$env:PYTHONPATH = (Resolve-Path .\src)
python -m russian_catalog_localizer.cli demo --out demo-output
```

Or install the CLI entry point:

```powershell
cd russian-catalog-localizer
python -m pip install -e .
rcl demo --out demo-output
```

Expected demo outputs:

- `demo-output/segments.ru.json`
- `demo-output/repaint_plan.json`
- `demo-output/qa_report.md`
- `demo-output/localized_package.zip`

The demo uses packaged synthetic fixtures, so it works from a source checkout or an installed wheel.

## Repository Layout

```text
russian-catalog-localizer/
  configs/localizer.example.toml
  docs/release.md
  docs/workflow.md
  examples/glossary.zh-ru.csv
  examples/sample_ocr_segments.json
  src/russian_catalog_localizer/
```

## CLI

```powershell
rcl demo --out demo-output
rcl ocr --input examples/sample_ocr_segments.json --out work/segments.json
rcl workflow --segments examples/sample_ocr_segments.json --glossary examples/glossary.zh-ru.csv --out work/run-001
rcl qa --segments work/run-001/segments.ru.json --out work/run-001/qa_report.md
rcl pack --source work/run-001 --out release/run-001.zip
```

The bundled OCR command normalizes an existing OCR JSON export. Real OCR backends such as Tesseract, RapidOCR, PaddleOCR, or cloud OCR should be added behind the same segment interface.

`segment = a text block plus page and bounding box / created by OCR or PDF text extraction / later steps repaint and QA these units.`

## Data Safety

- Keep source PDFs and page renders under ignored folders such as `data/`, `work/`, or `output/`.
- Keep API keys in environment variables or local secret stores, never in config files.
- Commit only small synthetic examples or properly licensed fixtures.
- Review `docs/release.md` before publishing a release package.

## License

MIT. See `LICENSE`.
