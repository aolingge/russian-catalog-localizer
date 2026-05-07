# Repository Agent Instructions

## Project Context

Repository: `aolingge/russian-catalog-localizer`
Primary language: Python

## Default Workflow

- Keep changes small and focused.
- Read `README.md`, `README.zh-CN.md`, `pyproject.toml`, and relevant `docs/` files before editing.
- Prefer the existing local-first pipeline: OCR segments, glossary, repaint plan, QA, sanitized package.
- Do not add customer PDFs, private OCR exports, real glossaries, API keys, cookies, credentials, private paths, local caches, or large binaries.
- Include verification commands in PR descriptions.

## Verification

- Default checks: `python -m pytest` and `python -m ruff check .`
- Release packaging changes should also run `tools/build_windows_package.ps1` on Windows when practical.

## Pull Request Rules

- CI and privacy checks must pass before merge.
- Release, packaging, OCR backend, customer-data handling, and credential-related changes require maintainer review.
