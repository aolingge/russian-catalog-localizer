# Russian Catalog Localizer

Open-source skeleton and Chinese Windows desktop assistant for localizing Chinese product-catalog OCR exports into Russian without committing private source PDFs, customer data, API keys, or large binary artifacts.

The pipeline shape is:

1. OCR Chinese PDF or page images into text segments with bounding boxes.
2. Apply a Chinese to Russian glossary before any machine translation.
3. Produce a repaint plan for overlay rendering or local patching.
4. Run QA for residual Chinese text and visual contact-sheet review.
5. Package only the safe release artifacts.

This repository includes a tiny synthetic sample. It does not include the original catalog PDF, customer-private OCR exports, or proprietary translation tables.

## Customer Quick Start

For non-technical Windows users, download the Windows package from the latest GitHub Release, extract it, and double-click `CatalogLocalizer.exe`. The app UI is Chinese and is intended to be used as a desktop assistant, not a command-line tool.

In the app:

1. Click `运行示例 Demo` first to verify the package.
2. For real data, select `OCR JSON`, `术语表 CSV`, and `输出目录`.
3. Click `运行 Workflow`.
4. Click `打开输出目录` to view the generated files.

Inputs:

- `OCR JSON`: an existing OCR export with page numbers, text, and bounding boxes.
- `术语表 CSV`: a Chinese-to-Russian glossary, using columns such as `source,target,note`.

Outputs are written to the selected output folder:

- `segments.ru.json` working file, which may contain source OCR text.
- `repaint_plan.json` working repaint plan, which may contain source OCR text.
- `qa_report.md` working QA report, which may contain residual source text.
- `localized_package.zip` sanitized sharing package.

Current limitation: this release does not directly OCR a PDF and does not render a finished localized PDF. It produces localized text segments, a repaint plan, a QA report, and a sanitized sharing zip. The public release package does not include customer PDFs, private OCR exports, private glossaries, credentials, cookies, or local caches.

Privacy note: treat the three working files as customer-private because they can contain source OCR text. `localized_package.zip` is generated from sanitized copies that remove OCR source text, glossary source terms, residual CJK snippets, and `source_text` fields.

Chinese customer instructions: `docs/customer-quick-start.zh-CN.md`.

## Developer Quick Start

Run from a source checkout:

```powershell
cd russian-catalog-localizer
$env:PYTHONPATH = (Resolve-Path .\src)
python -m russian_catalog_localizer
```

To run the CLI demo:

```powershell
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
rcl-gui
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
