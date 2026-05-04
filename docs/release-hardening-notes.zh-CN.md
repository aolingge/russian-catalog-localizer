# 发布硬化经验

这份笔记记录 v0.2.0 做中文桌面交付包时沉淀下来的可复用规则。

## 桌面交付

- 客户包应优先提供独立 EXE 和中文说明，客户路径不应依赖 `PYTHONPATH`、源码目录或命令行知识。
- PyInstaller 的 smoke test 要运行打包后的 EXE，而不是只跑源码入口。
- Windows PowerShell 5 对命令行引号和 .NET API 支持更保守：复杂 Python probe 写临时 `.py` 文件执行，进程参数用 `ProcessStartInfo.Arguments`。
- 打包脚本要捕获 stdout/stderr；失败时输出日志尾部，避免 windowed EXE 静默失败。
- Tcl/Tk 桌面包要显式探测并加入 Python `DLLs`、Conda `Library\bin`、`tcl`、`Library\lib` 下的 Tcl/Tk 运行时。

## 数据安全

- 工作文件和分享包必须分离：工作文件可保留 OCR 原文以支持后续排版，分享包只放脱敏副本。
- 脱敏分享包不得包含源 OCR 文本、中文源术语、残留中文片段、`source_text` 字段、真实术语表、PDF、图片、缓存或凭据。
- 发布包只复制精确 synthetic fixture 文件，不复制整个 `examples` 目录。
- 打包器优先白名单；黑名单只作为额外保护，不能作为公开发布的唯一安全边界。
- 文档必须如实说明当前能力：本版本处理 OCR JSON 和术语表 CSV，不直接 OCR PDF，也不直接生成最终 PDF。

## 验收

- 每次发布至少跑：`compileall`、`unittest`、`ruff`、CLI workflow、GUI `--demo-out`、PyInstaller package build。
- 公开 zip 要审计文件清单，确认不含客户数据、缓存、密钥、图片、PDF 或真实运行输出。
- 程序生成的 `localized_package.zip` 要解包检查，确认只含脱敏 `qa_report.md`、`repaint_plan.json`、`segments.ru.json`。
