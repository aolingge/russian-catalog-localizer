# Release Guide

Use this checklist before making a public release or sharing an artifact outside the local machine.

## Source Control

- Confirm `git status` contains only intended open-source files.
- Confirm no source PDF, rendered page image dump, private cache, or customer translation table is staged.
- Confirm `.gitignore` covers `data/`, `work/`, `output/`, `release/`, PDFs, archives, and local secrets.
- Run a secret scan if available.

## Build And Smoke Test

```powershell
python -m compileall src
$env:PYTHONPATH = (Resolve-Path .\src)
python -m russian_catalog_localizer.cli demo --out work/demo-smoke
```

Check `work/demo-smoke/qa_report.md`. The synthetic demo should report zero residual Chinese hits.
Delete generated smoke-test artifacts and `__pycache__/` directories before publishing a source tree.

## Artifact Packaging

Package generated outputs, not private sources:

```powershell
rcl pack --source work/run-001 --out release/run-001.zip
```

Before upload, inspect the zip contents:

```powershell
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile

with ZipFile(Path("release/run-001.zip")) as zf:
    for name in zf.namelist():
        print(name)
PY
```

Do not publish files that contain:

- API keys, tokens, cookies, or connection strings.
- Customer names or private contacts unless explicitly approved.
- Full source PDFs, OCR dumps, or high-resolution page renders.
- Translation memory copied from a private engagement.

## Version Notes

Update `CHANGELOG.md` for every release. Use small, factual entries that describe public behavior and avoid private customer context.
