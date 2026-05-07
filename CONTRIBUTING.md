# Contributing

Thanks for improving `russian-catalog-localizer`. This repository is privacy-sensitive because localization inputs may come from customer catalogs, OCR exports, and glossaries.

## Good Contributions

- Improve the synthetic demo and fixtures.
- Add OCR backend adapters behind the existing segment interface.
- Improve glossary handling and QA checks.
- Improve Chinese customer documentation.
- Add tests for privacy-safe packaging and residual Chinese detection.
- Improve release packaging scripts without adding private data.

## Local Checks

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

## Safety Rules

- Do not commit customer PDFs, page images, OCR exports, real glossaries, API keys, cookies, credentials, private paths, or local caches.
- Use only synthetic or explicitly licensed examples.
- Treat `segments.ru.json`, `repaint_plan.json`, and `qa_report.md` as private working files when they come from real customer data.
- Only `localized_package.zip` is intended for sanitized sharing, and it must be reviewed before release.

## Pull Request Checklist

- [ ] Tests or fixtures cover the changed behavior.
- [ ] `python -m pytest` passed or the reason it could not run is explained.
- [ ] No customer-private data or real credentials were added.
- [ ] Documentation was updated if workflow, CLI, GUI, or release behavior changed.
