# 客户快速开始：中文桌面助手

这个包是 Windows 中文桌面助手，用来把已经 OCR 出来的中文目录文字片段，按术语表处理成俄文分段、重绘计划和 QA 报告。客户不需要安装 Python，也不需要运行命令行。

请先确认交付包里有 `CatalogLocalizer.exe`。公共交付包只包含程序、示例和说明，不包含客户 PDF、真实 OCR 原始文件、真实术语表、密钥、Cookie、账号信息或本地缓存。

## 最简单用法

1. 解压 `russian-catalog-localizer-desktop-v0.2.1-windows.zip`。
2. 双击 `CatalogLocalizer.exe`。
3. 界面打开后会显示 `俄文目录本地化助手`。第一次使用请先点 `试运行 Demo`。
4. Demo 会自动使用内置示例数据。输出目录默认是文档目录下的 `俄文目录输出` 文件夹。
5. 如果 QA 摘要里显示 `残留中文: 0`，并列出四个输出文件，说明软件运行正常。
6. 点 `打开输出` 可以查看 Demo 结果；点 `打开 QA` 可以直接看检查报告。

## 处理客户自己的数据

准备两个输入文件：

- `OCR JSON`：OCR 后的文字片段文件。每个片段需要包含页码、文字和坐标。
- `术语表 CSV`：中文到俄文术语表，推荐列名是 `source,target,note`，其中 `source` 是中文，`target` 是俄文。

在桌面助手里按顺序选择：

1. `OCR JSON` 这一行点 `选择 JSON`，选 OCR JSON 文件。
2. `术语表 CSV` 这一行点 `选择 CSV`，选术语表 CSV 文件。
3. `输出目录` 这一行可以保留默认目录，也可以点 `选择文件夹` 换位置。
4. 文件都显示 `已选择` 后，点 `开始生成`。
5. 完成后点 `打开输出` 查看结果，或点 `复制分享包路径` 发给后续人员。

`OCR JSON = 带页码和坐标的文字块文件 / 由 OCR 或 PDF 文本提取工具生成 / 软件根据它生成俄文文本和重绘计划。`

`术语表 CSV = 逗号分隔表格文件 / 告诉软件哪些中文词要替换成哪些俄文词 / 术语表越完整，输出里的残留中文越少。`

## 输出文件

运行后会在选择的 `输出目录` 里生成：

- `segments.ru.json`：完整工作文件，给维护人员继续排版用，可能包含原 OCR 文本。
- `repaint_plan.json`：完整工作重绘计划，给后续排版/重绘工具使用，可能包含原 OCR 文本。
- `qa_report.md`：完整残留中文检查报告，残留项会列出文本，属于私有工作文件。
- `localized_package.zip`：脱敏后的分享包，只保留俄文文本、坐标、计数和状态。

`localized_package.zip` 默认不会把客户原始 PDF、图片、OCR 原始文件、术语表、源中文术语或残留中文文本一起放进去。输出目录里的三个完整工作文件仍应按客户资料管理，不要公开上传。

## 当前版本能做什么

- 一键运行内置示例 Demo，用来确认程序能启动并生成结果。
- 读取客户准备好的 OCR JSON。
- 使用术语表把中文术语替换成俄文。
- 生成完整 QA 报告，并额外生成脱敏分享包。
- 自动过滤常见私密文件和大文件，降低误打包风险。

## 当前限制

- 当前版本不直接 OCR PDF，也不直接读取客户 PDF 生成 OCR 结果。
- 当前版本不直接输出最终俄文 PDF。
- 如果客户只有 PDF，需要先用 OCR 工具导出 JSON，或由后续版本接入 OCR/PDF 渲染模块。
- `qa_report.md` 检查的是文本片段里的残留中文；最终排版图仍建议人工抽查。

## 维护人员打包

在源码仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_windows_package.ps1
```

默认输出：

- `release\russian-catalog-localizer-desktop-v0.2.1-windows\`
- `release\russian-catalog-localizer-desktop-v0.2.1-windows.zip`

打包脚本会自动构建独立 EXE，并运行一次内置 demo smoke test。

`smoke test = 最小冒烟测试 / 用来确认软件包能启动并生成关键文件 / 失败就不能交付。`

## 交付前检查

- 解压 zip 后双击 EXE 可打开中文界面。
- 点 `试运行 Demo` 后能生成四个输出文件。
- `qa_report.md` 显示 `Residual Chinese hits: 0`。
- `localized_package.zip` 里只包含脱敏后的 `qa_report.md`、`repaint_plan.json`、`segments.ru.json`。
- 打开 `localized_package.zip` 抽查，里面不能出现客户原 OCR 中文、中文源术语、真实术语表或 `source_text` 字段。
- 公共发布包里不能包含客户 PDF、真实 OCR 原始文件、真实术语表、密钥、Cookie、账号信息或本地缓存。
