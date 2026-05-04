# Changelog

All notable changes to this project will be documented here.

The format follows Keep a Changelog, and this project uses semantic versioning once releases begin.

## [0.2.1] - 2026-05-05

### Changed

- Redesigned the Chinese desktop app into a simpler three-step workspace.
- Added clearer input state labels, result cards, progress feedback, QA opening, and share-package path copying.
- Updated customer wording to match the polished buttons: `试运行 Demo`, `开始生成`, `打开输出`, and `打开 QA`.

## [0.2.0] - 2026-05-05

### Added

- Chinese Tkinter desktop app for one-click demo and guided workflow runs.
- Windows PyInstaller packaging script that builds a standalone EXE customer bundle.
- Chinese customer quick-start documentation.
- Shared workflow module used by CLI and GUI.
- Package smoke-test mode for the desktop executable.

### Changed

- CLI workflow now calls the shared workflow implementation.
- Safe packager excludes more private file types, including `.env*`, PDFs, images, and archive files.
- Customer-facing documentation now states the exact desktop entry point, required inputs, output folder contents, Demo flow, current PDF/OCR limitations, and private-data exclusions.
- `localized_package.zip` now contains sanitized sharing artifacts instead of full working files.

## [0.1.0] - 2026-05-05

### Added

- Initial open-source repository skeleton.
- Standard-library CLI for demo, OCR JSON normalization, glossary localization, QA, repaint plans, and safe packaging.
- Synthetic Chinese to Russian sample OCR segments and glossary.
- Workflow and release documentation focused on avoiding private data and large source PDFs.
