# Workflow

This project turns a catalog localization run into small, composable steps. The default implementation is intentionally local and conservative so the public repository can be shared without private source files.

## 1. OCR

Input can be a PDF, page images, or an existing OCR export. The public skeleton uses JSON OCR exports shaped like:

```json
{
  "segments": [
    {
      "page": 1,
      "text": "额定电压",
      "bbox": [72, 132, 160, 152],
      "confidence": 0.94
    }
  ]
}
```

`bbox = x0, y0, x1, y1 coordinates / tells the renderer where the text lives / keeps translation tied to page layout.`

Recommended adapters:

- RapidOCR or PaddleOCR for image-heavy pages.
- Tesseract for residual Chinese QA checks.
- `pdftotext` or PyMuPDF for selectable PDF text.

Do not commit source PDFs or full page renders. Keep them in `data/`, `work/`, or another ignored folder.

## 2. Glossary First

Run glossary replacement before machine translation. This stabilizes product names, electrical terms, and recurring table headers.

```powershell
rcl workflow --segments examples/sample_ocr_segments.json --glossary examples/glossary.zh-ru.csv --out work/run-001
```

The sample glossary is synthetic and safe to publish. Real customer terminology should stay in a private repository or be reduced to a sanitized fixture.

## 3. Repaint Plan

The CLI writes `repaint_plan.json`. It is a renderer-neutral manifest containing page, source text, translated text, and bounding boxes.

Use this plan to drive a renderer such as:

- ReportLab overlay drawing.
- PyMuPDF redaction plus insertion.
- Image patching for flattened scans.
- A design-tool pipeline for manual review.

Keep page-specific hand repairs as data files or small renderer plugins. Avoid copying customer-specific page logic into the public core.

## 4. QA

The bundled QA step scans localized segments for residual CJK characters and writes a Markdown report. A production workflow should add:

- Contact sheets for visual comparison.
- OCR residual checks against the final PDF.
- Font coverage checks for Cyrillic text.
- Page count and package manifest validation.

```powershell
rcl qa --segments work/run-001/segments.ru.json --out work/run-001/qa_report.md
```

## 5. Package

The packager creates a zip while skipping common secret files and files over the configured size limit.

```powershell
rcl pack --source work/run-001 --out release/run-001.zip
```

Review every release archive before publishing.
