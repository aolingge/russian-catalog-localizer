# Russian Catalog Localizer

语言： [English](README.md) | 简体中文

一个面向中文 Windows 用户的俄文目录本地化桌面助手和本地优先处理管线。它用于把中文产品目录 OCR 导出的文字片段处理成俄文分段、重绘计划、QA 报告和脱敏分享包，同时避免把客户 PDF、私有 OCR 原文、术语表、API key 或大文件提交到公开仓库。

## 处理流程

1. 将中文 PDF 或页面图片 OCR 成带页码、文本和坐标的片段。
2. 在机器翻译或术语替换前先应用中俄术语表。
3. 生成用于叠字/重绘的 repaint plan。
4. 检查残留中文，并生成视觉抽查用的 QA 材料。
5. 只打包可安全分享的脱敏交付物。

本仓库只包含极小的合成示例，不包含原始客户目录、私有 OCR 导出或专有术语表。

## 客户快速开始

非技术 Windows 用户请从最新 GitHub Release 下载 Windows 包，解压后双击 `CatalogLocalizer.exe`。桌面界面是中文，目标是作为本地助手使用，而不是命令行工具。

在应用里：

1. 先点击 `试运行 Demo` 验证软件包。
2. 处理真实数据时，选择 `OCR JSON`、`术语表 CSV` 和 `输出目录`。
3. 点击 `开始生成`。
4. 点击 `打开输出` 或 `打开 QA` 查看结果。

更详细说明见 [客户快速开始](docs/customer-quick-start.zh-CN.md)。

## 开发者快速开始

从源码运行桌面应用：

```powershell
cd russian-catalog-localizer
$env:PYTHONPATH = (Resolve-Path .\src)
python -m russian_catalog_localizer
```

运行 CLI demo：

```powershell
python -m russian_catalog_localizer.cli demo --out demo-output
```

安装本地 CLI 入口：

```powershell
python -m pip install -e .
rcl demo --out demo-output
```

预期输出：

- `demo-output/segments.ru.json`
- `demo-output/repaint_plan.json`
- `demo-output/qa_report.md`
- `demo-output/localized_package.zip`

## CLI

```powershell
rcl demo --out demo-output
rcl-gui
rcl ocr --input examples/sample_ocr_segments.json --out work/segments.json
rcl workflow --segments examples/sample_ocr_segments.json --glossary examples/glossary.zh-ru.csv --out work/run-001
rcl qa --segments work/run-001/segments.ru.json --out work/run-001/qa_report.md
rcl pack --source work/run-001 --out release/run-001.zip
```

`segment = 带文本、页码和坐标的文字块 / 由 OCR 或 PDF 文本提取生成 / 后续步骤会基于它做重绘计划和 QA。`

## 数据安全

- 原始 PDF、页面渲染图和私有 OCR 文件放在 `data/`、`work/`、`output/` 等忽略目录。
- API key 只放在环境变量或本地密钥管理工具里，不写入配置文件。
- 只提交小型合成示例或授权明确的公开 fixtures。
- 发布前阅读 [release checklist](docs/release.md) 和 [release hardening notes](docs/release-hardening-notes.zh-CN.md)。

## 验证

```bash
python -m pytest
python -m ruff check .
```

## License

MIT. See [LICENSE](LICENSE).
