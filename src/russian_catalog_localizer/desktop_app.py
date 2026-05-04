from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from .workflow import run_localization_workflow

APP_TITLE = "俄文目录本地化助手"
DEFAULT_OUTPUT_FOLDER = "俄文目录输出"
UI_FONT = "Microsoft YaHei UI" if os.name == "nt" else ""


@dataclass(frozen=True)
class WorkflowResult:
    output_dir: Path
    segments_path: Path
    repaint_plan_path: Path
    qa_report_path: Path
    package_path: Path
    segment_count: int
    residual_cjk_count: int
    packaged_files: tuple[str, ...]
    qa_summary: str


@dataclass(frozen=True)
class WorkflowInput:
    segments_path: Path
    glossary_path: Path
    output_dir: Path


def default_output_dir() -> Path:
    documents = Path.home() / "Documents"
    if documents.exists():
        return documents / DEFAULT_OUTPUT_FOLDER
    return Path.cwd() / "desktop-output"


def validate_workflow_inputs(
    segments_value: str,
    glossary_value: str,
    output_value: str,
) -> WorkflowInput:
    errors: list[str] = []
    segments_path = Path(segments_value.strip()).expanduser() if segments_value.strip() else None
    glossary_path = Path(glossary_value.strip()).expanduser() if glossary_value.strip() else None
    output_dir = Path(output_value.strip()).expanduser() if output_value.strip() else None

    if segments_path is None:
        errors.append("请选择 OCR JSON 文件。")
    elif not segments_path.is_file():
        errors.append(f"OCR JSON 不存在：{segments_path}")
    elif segments_path.suffix.lower() != ".json":
        errors.append("OCR 文件需要是 .json 格式。")

    if glossary_path is None:
        errors.append("请选择术语表 CSV 文件。")
    elif not glossary_path.is_file():
        errors.append(f"术语表 CSV 不存在：{glossary_path}")
    elif glossary_path.suffix.lower() != ".csv":
        errors.append("术语表需要是 .csv 格式。")

    if output_dir is None:
        errors.append("请选择输出目录。")

    if errors:
        raise ValueError("\n".join(errors))

    assert segments_path is not None
    assert glossary_path is not None
    assert output_dir is not None
    return WorkflowInput(segments_path, glossary_path, output_dir)


def run_desktop_workflow(segments_path: Path, glossary_path: Path, out_dir: Path) -> WorkflowResult:
    """Run the same local pipeline as the CLI and return GUI-friendly metadata."""
    pipeline_result = run_localization_workflow(segments_path, glossary_path, out_dir)
    qa_summary = build_qa_summary(
        segment_count=pipeline_result.segment_count,
        residual_cjk_count=pipeline_result.residual_chinese_count,
        qa_report_path=pipeline_result.qa_report,
        package_path=pipeline_result.package_zip,
        packaged_files=pipeline_result.packaged_files,
    )

    return WorkflowResult(
        output_dir=pipeline_result.output_dir,
        segments_path=pipeline_result.localized_segments,
        repaint_plan_path=pipeline_result.repaint_plan,
        qa_report_path=pipeline_result.qa_report,
        package_path=pipeline_result.package_zip,
        segment_count=pipeline_result.segment_count,
        residual_cjk_count=pipeline_result.residual_chinese_count,
        packaged_files=pipeline_result.packaged_files,
        qa_summary=qa_summary,
    )


def build_qa_summary(
    *,
    segment_count: int,
    residual_cjk_count: int,
    qa_report_path: Path,
    package_path: Path,
    packaged_files: tuple[str, ...],
) -> str:
    report_text = qa_report_path.read_text(encoding="utf-8") if qa_report_path.exists() else ""
    important_lines: list[str] = []
    for line in report_text.splitlines():
        if (
            line.startswith("- Segments checked:")
            or line.startswith("- Residual Chinese hits:")
            or line.startswith("No residual CJK")
            or line.startswith("### Page ")
            or line.startswith("- `")
        ):
            important_lines.append(line)

    if not important_lines:
        important_lines = [
            f"- Segments checked: {segment_count}",
            f"- Residual Chinese hits: {residual_cjk_count}",
        ]

    status = "通过，可以查看分享包。" if residual_cjk_count == 0 else "需要补充术语或人工复核。"
    packaged_preview = ", ".join(packaged_files[:4]) if packaged_files else "无"
    if len(packaged_files) > 4:
        packaged_preview = f"{packaged_preview}, ..."

    return "\n".join(
        [
            "QA 摘要",
            f"- 状态: {status}",
            f"- 分段总数: {segment_count}",
            f"- 残留中文: {residual_cjk_count}",
            f"- 分享包: {package_path.name}",
            f"- 包内预览: {packaged_preview}",
            "",
            *important_lines,
        ]
    )


def build_result_message(result: WorkflowResult) -> str:
    next_step = "可以把脱敏分享包发给后续排版或复核人员。"
    if result.residual_cjk_count:
        next_step = "建议先补充术语表或人工处理残留中文，再发送分享包。"

    return "\n".join(
        [
            result.qa_summary,
            "",
            "输出文件",
            f"- 完整俄文分段: {result.segments_path}",
            f"- 完整重绘计划: {result.repaint_plan_path}",
            f"- 完整 QA 报告: {result.qa_report_path}",
            f"- 脱敏分享包: {result.package_path}",
            "",
            f"下一步: {next_step}",
        ]
    )


@contextmanager
def demo_resource_paths() -> Any:
    example_dir = files("russian_catalog_localizer").joinpath("examples")
    with (
        as_file(example_dir.joinpath("sample_ocr_segments.json")) as segments_path,
        as_file(example_dir.joinpath("glossary.zh-ru.csv")) as glossary_path,
    ):
        yield segments_path, glossary_path


def open_path(path: Path) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])


def open_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    open_path(path)


def _load_tk() -> tuple[Any, Any, Any, Any, Any]:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    return tk, ttk, filedialog, messagebox, scrolledtext


class CatalogLocalizerApp:
    def __init__(
        self,
        root: Any,
        *,
        tk_module: Any,
        ttk_module: Any,
        filedialog_module: Any,
        messagebox_module: Any,
        scrolledtext_module: Any,
    ) -> None:
        self.root = root
        self.tk = tk_module
        self.ttk = ttk_module
        self.filedialog = filedialog_module
        self.messagebox = messagebox_module
        self.scrolledtext = scrolledtext_module

        self.ocr_json_var = self.tk.StringVar()
        self.glossary_csv_var = self.tk.StringVar()
        self.output_dir_var = self.tk.StringVar(value=str(default_output_dir()))
        self.status_var = self.tk.StringVar(value="准备就绪")
        self.step_var = self.tk.StringVar(value="第 1 步：选择 OCR JSON 和术语表 CSV")
        self.ocr_state_var = self.tk.StringVar(value="未选择")
        self.glossary_state_var = self.tk.StringVar(value="未选择")
        self.output_state_var = self.tk.StringVar(value="默认输出目录")
        self.result_state_var = self.tk.StringVar(value="未运行")
        self.segment_count_var = self.tk.StringVar(value="-")
        self.residual_count_var = self.tk.StringVar(value="-")
        self.package_name_var = self.tk.StringVar(value="-")

        self._busy = False
        self._last_result: WorkflowResult | None = None

        self.root.title(APP_TITLE)
        self.root.geometry("1040x700")
        self.root.minsize(900, 620)
        self._configure_style()
        self._build_layout()
        self._update_input_states()

    def _configure_style(self) -> None:
        style = self.ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except self.tk.TclError:
            pass

        palette = {
            "bg": "#f3f6f7",
            "surface": "#ffffff",
            "ink": "#172126",
            "muted": "#5b6770",
            "line": "#d8e0e4",
            "primary": "#116a71",
            "primary_hover": "#0d555b",
            "soft": "#e8f2f3",
            "warn": "#8a5a00",
        }
        self.root.configure(bg=palette["bg"])
        style.configure("App.TFrame", background=palette["bg"])
        style.configure("Surface.TFrame", background=palette["surface"], relief="flat")
        style.configure("Hero.TFrame", background=palette["primary"])
        style.configure(
            "Card.TFrame",
            background=palette["surface"],
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Title.TLabel",
            background=palette["primary"],
            foreground="#ffffff",
            font=(UI_FONT, 22, "bold"),
        )
        style.configure(
            "HeroText.TLabel",
            background=palette["primary"],
            foreground="#e4f5f6",
            font=(UI_FONT, 10),
        )
        style.configure(
            "Section.TLabel",
            background=palette["surface"],
            foreground=palette["ink"],
            font=(UI_FONT, 12, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=palette["surface"],
            foreground=palette["ink"],
            font=(UI_FONT, 10),
        )
        style.configure(
            "Muted.TLabel",
            background=palette["surface"],
            foreground=palette["muted"],
            font=(UI_FONT, 9),
        )
        style.configure(
            "Metric.TLabel",
            background=palette["surface"],
            foreground=palette["primary"],
            font=(UI_FONT, 18, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=palette["soft"],
            foreground=palette["primary"],
            font=(UI_FONT, 10, "bold"),
        )
        style.configure(
            "Warning.TLabel",
            background=palette["surface"],
            foreground=palette["warn"],
            font=(UI_FONT, 9),
        )
        style.configure("Primary.TButton", font=(UI_FONT, 11, "bold"), padding=(18, 10))
        style.map("Primary.TButton", background=[("active", palette["primary_hover"])])
        style.configure("Secondary.TButton", padding=(14, 8))
        style.configure("Path.TEntry", padding=6)
        style.configure(
            "TProgressbar",
            background=palette["primary"],
            troughcolor=palette["soft"],
        )

    def _build_layout(self) -> None:
        root_frame = self.ttk.Frame(self.root, style="App.TFrame", padding=18)
        root_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        root_frame.columnconfigure(0, weight=3)
        root_frame.columnconfigure(1, weight=2)
        root_frame.rowconfigure(1, weight=1)

        self._build_hero(root_frame)
        self._build_work_area(root_frame)
        self._build_result_area(root_frame)

    def _build_hero(self, parent: Any) -> None:
        hero = self.ttk.Frame(parent, style="Hero.TFrame", padding=18)
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        hero.columnconfigure(0, weight=1)

        title = self.ttk.Label(hero, text=APP_TITLE, style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        subtitle = self.ttk.Label(
            hero,
            text="三步完成：选择文件，点击生成，打开结果。当前处理 OCR JSON 和术语表 CSV。",
            style="HeroText.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 0))
        status = self.ttk.Label(
            hero,
            textvariable=self.status_var,
            style="HeroText.TLabel",
            anchor="e",
        )
        status.grid(row=0, column=1, rowspan=2, sticky="e", padx=(18, 0))

    def _build_work_area(self, parent: Any) -> None:
        work = self.ttk.Frame(parent, style="Surface.TFrame", padding=16)
        work.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        work.columnconfigure(0, weight=1)
        work.rowconfigure(6, weight=1)

        self.ttk.Label(work, textvariable=self.step_var, style="Section.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.ttk.Label(
            work,
            text="客户只需要准备两个文件。输出目录已自动填好，也可以自己选择。",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self._add_picker_card(
            work,
            row=2,
            title="1. OCR JSON",
            hint="带页码、文字和坐标的 OCR 结果文件。",
            variable=self.ocr_json_var,
            state_variable=self.ocr_state_var,
            command=self._choose_ocr_json,
            button_text="选择 JSON",
        )
        self._add_picker_card(
            work,
            row=3,
            title="2. 术语表 CSV",
            hint="source,target,note 三列的中文到俄文术语表。",
            variable=self.glossary_csv_var,
            state_variable=self.glossary_state_var,
            command=self._choose_glossary_csv,
            button_text="选择 CSV",
        )
        self._add_picker_card(
            work,
            row=4,
            title="3. 输出目录",
            hint="生成的工作文件和脱敏分享包会放在这里。",
            variable=self.output_dir_var,
            state_variable=self.output_state_var,
            command=self._choose_output_dir,
            button_text="选择文件夹",
        )

        actions = self.ttk.Frame(work, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(16, 10))
        actions.columnconfigure(4, weight=1)

        self.run_button = self.ttk.Button(
            actions,
            text="开始生成",
            style="Primary.TButton",
            command=self._run_from_form,
        )
        self.run_button.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.demo_button = self.ttk.Button(
            actions,
            text="试运行 Demo",
            style="Secondary.TButton",
            command=self._run_demo,
        )
        self.demo_button.grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.reset_button = self.ttk.Button(
            actions,
            text="重置",
            style="Secondary.TButton",
            command=self._reset_form,
        )
        self.reset_button.grid(row=0, column=2, sticky="w")
        self.ready_label = self.ttk.Label(actions, text="", style="Warning.TLabel", anchor="e")
        self.ready_label.grid(row=0, column=4, sticky="ew")

        self.progress = self.ttk.Progressbar(work, mode="indeterminate")
        self.progress.grid(row=6, column=0, sticky="ew", pady=(6, 0))
        self.progress.grid_remove()

    def _build_result_area(self, parent: Any) -> None:
        result = self.ttk.Frame(parent, style="Surface.TFrame", padding=16)
        result.grid(row=1, column=1, sticky="nsew")
        result.columnconfigure(0, weight=1)
        result.rowconfigure(3, weight=1)

        self.ttk.Label(result, text="结果", style="Section.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.ttk.Label(
            result,
            text="生成完成后，这里会显示是否还有残留中文，以及可以分享的压缩包。",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        metrics = self.ttk.Frame(result, style="Surface.TFrame")
        metrics.grid(row=2, column=0, sticky="ew")
        metrics.columnconfigure((0, 1), weight=1)
        self._add_metric_card(
            metrics,
            row=0,
            column=0,
            label="状态",
            variable=self.result_state_var,
        )
        self._add_metric_card(
            metrics,
            row=0,
            column=1,
            label="分段",
            variable=self.segment_count_var,
        )
        self._add_metric_card(
            metrics,
            row=1,
            column=0,
            label="残留中文",
            variable=self.residual_count_var,
        )
        self._add_metric_card(
            metrics,
            row=1,
            column=1,
            label="分享包",
            variable=self.package_name_var,
        )

        summary_frame = self.ttk.Frame(result, style="Surface.TFrame")
        summary_frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(1, weight=1)
        self.ttk.Label(summary_frame, text="操作摘要", style="Section.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.summary_text = self.scrolledtext.ScrolledText(
            summary_frame,
            height=14,
            wrap=self.tk.WORD,
            state="disabled",
            bg="#fbfcfc",
            fg="#172126",
            relief="flat",
            padx=10,
            pady=10,
        )
        self.summary_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        result_actions = self.ttk.Frame(result, style="Surface.TFrame")
        result_actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        result_actions.columnconfigure(3, weight=1)
        self.open_button = self.ttk.Button(
            result_actions,
            text="打开输出",
            style="Secondary.TButton",
            command=self._open_output_dir,
        )
        self.open_button.grid(row=0, column=0, padx=(0, 8))
        self.open_qa_button = self.ttk.Button(
            result_actions,
            text="打开 QA",
            style="Secondary.TButton",
            command=self._open_qa_report,
        )
        self.open_qa_button.grid(row=0, column=1, padx=(0, 8))
        self.copy_package_button = self.ttk.Button(
            result_actions,
            text="复制分享包路径",
            style="Secondary.TButton",
            command=self._copy_package_path,
        )
        self.copy_package_button.grid(row=0, column=2, padx=(0, 8))

        self._write_summary(
            "先点击“试运行 Demo”确认软件正常。\n\n"
            "处理自己的资料时，只需要选 OCR JSON、术语表 CSV，然后点击“开始生成”。"
        )

    def _add_picker_card(
        self,
        parent: Any,
        *,
        row: int,
        title: str,
        hint: str,
        variable: Any,
        state_variable: Any,
        command: Callable[[], None],
        button_text: str,
    ) -> None:
        card = self.ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.columnconfigure(1, weight=1)
        self.ttk.Label(card, text=title, style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.ttk.Label(card, textvariable=state_variable, style="Status.TLabel").grid(
            row=0,
            column=2,
            sticky="e",
            padx=(10, 0),
        )
        self.ttk.Label(card, text=hint, style="Muted.TLabel").grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(3, 8),
        )
        entry = self.ttk.Entry(card, textvariable=variable, style="Path.TEntry")
        entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self.ttk.Button(card, text=button_text, command=command).grid(row=2, column=2, sticky="e")

    def _add_metric_card(
        self,
        parent: Any,
        *,
        row: int,
        column: int,
        label: str,
        variable: Any,
    ) -> None:
        card = self.ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 8, 0),
            pady=(0, 8),
        )
        card.columnconfigure(0, weight=1)
        self.ttk.Label(card, text=label, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.ttk.Label(card, textvariable=variable, style="Metric.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

    def _choose_ocr_json(self) -> None:
        path = self.filedialog.askopenfilename(
            title="选择 OCR JSON",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self.ocr_json_var.set(path)
            self._update_input_states()

    def _choose_glossary_csv(self) -> None:
        path = self.filedialog.askopenfilename(
            title="选择术语表 CSV",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if path:
            self.glossary_csv_var.set(path)
            self._update_input_states()

    def _choose_output_dir(self) -> None:
        path = self.filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)
            self._update_input_states()

    def _run_from_form(self) -> None:
        try:
            workflow_input = validate_workflow_inputs(
                self.ocr_json_var.get(),
                self.glossary_csv_var.get(),
                self.output_dir_var.get(),
            )
        except ValueError as exc:
            self._show_error("还不能开始", f"{exc}\n\n请按 1、2、3 的顺序补齐文件。")
            self._update_input_states()
            return

        self._start_worker(
            "正在生成，请稍等...",
            lambda: run_desktop_workflow(
                workflow_input.segments_path,
                workflow_input.glossary_path,
                workflow_input.output_dir,
            ),
        )

    def _run_demo(self) -> None:
        output_dir = Path(self.output_dir_var.get() or default_output_dir()).expanduser()
        self.output_dir_var.set(str(output_dir))
        self._update_input_states()

        def task() -> WorkflowResult:
            with demo_resource_paths() as (segments_path, glossary_path):
                return run_desktop_workflow(segments_path, glossary_path, output_dir)

        self._start_worker("正在运行 Demo，请稍等...", task)

    def _start_worker(self, status: str, task: Callable[[], WorkflowResult]) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self.status_var.set(status)
        self.result_state_var.set("运行中")
        self.step_var.set("第 2 步：正在生成结果")
        self._write_summary(status)

        def worker() -> None:
            try:
                result = task()
            except Exception as error:  # pragma: no cover - exercised through GUI error path.
                self.root.after(0, lambda error=error: self._on_worker_error(error))
                return
            self.root.after(0, lambda: self._on_worker_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_worker_success(self, result: WorkflowResult) -> None:
        self._last_result = result
        self._set_busy(False)
        self.status_var.set("完成")
        self.step_var.set("第 3 步：查看结果")
        self.result_state_var.set("通过" if result.residual_cjk_count == 0 else "需复核")
        self.segment_count_var.set(str(result.segment_count))
        self.residual_count_var.set(str(result.residual_cjk_count))
        self.package_name_var.set(result.package_path.name)
        self.output_dir_var.set(str(result.output_dir))
        self._write_summary(build_result_message(result))
        self._update_input_states()

    def _on_worker_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("运行失败")
        self.step_var.set("第 1 步：检查输入后重试")
        self.result_state_var.set("失败")
        message = f"运行失败：{exc}\n\n请检查 OCR JSON 格式、术语表列名和输出目录权限。"
        self._write_summary(message)
        self._show_error("运行失败", message)

    def _open_output_dir(self) -> None:
        target = (
            self._last_result.output_dir
            if self._last_result
            else Path(self.output_dir_var.get()).expanduser()
        )
        try:
            open_directory(target)
        except Exception as exc:  # pragma: no cover - depends on desktop integration.
            self._show_error("无法打开输出目录", str(exc))

    def _open_qa_report(self) -> None:
        if not self._last_result:
            self._show_error("还没有 QA 报告", "请先运行 Demo 或开始生成。")
            return
        try:
            open_path(self._last_result.qa_report_path)
        except Exception as exc:  # pragma: no cover - depends on desktop integration.
            self._show_error("无法打开 QA 报告", str(exc))

    def _copy_package_path(self) -> None:
        if not self._last_result:
            self._show_error("还没有分享包", "请先运行 Demo 或开始生成。")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(str(self._last_result.package_path))
        self.status_var.set("已复制分享包路径")

    def _reset_form(self) -> None:
        self.ocr_json_var.set("")
        self.glossary_csv_var.set("")
        self.output_dir_var.set(str(default_output_dir()))
        self._last_result = None
        self.status_var.set("准备就绪")
        self.step_var.set("第 1 步：选择 OCR JSON 和术语表 CSV")
        self.result_state_var.set("未运行")
        self.segment_count_var.set("-")
        self.residual_count_var.set("-")
        self.package_name_var.set("-")
        self._write_summary("已重置。可以先运行 Demo，或选择客户自己的 OCR JSON 和术语表 CSV。")
        self._update_input_states()

    def _write_summary(self, text: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", self.tk.END)
        if text:
            self.summary_text.insert(self.tk.END, text)
        self.summary_text.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for button in (
            self.run_button,
            self.demo_button,
            self.reset_button,
            self.open_button,
            self.open_qa_button,
            self.copy_package_button,
        ):
            button.configure(state=state)
        if busy:
            self.progress.grid()
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.grid_remove()
            self._update_input_states()

    def _update_input_states(self) -> None:
        segments = self.ocr_json_var.get().strip()
        glossary = self.glossary_csv_var.get().strip()
        output = self.output_dir_var.get().strip()

        self.ocr_state_var.set(self._file_state(segments, ".json"))
        self.glossary_state_var.set(self._file_state(glossary, ".csv"))
        self.output_state_var.set("已选择" if output else "未选择")

        can_run = (
            bool(segments)
            and bool(glossary)
            and bool(output)
            and Path(segments).expanduser().is_file()
            and Path(glossary).expanduser().is_file()
        )
        self.run_button.configure(state=("normal" if can_run and not self._busy else "disabled"))
        if can_run:
            self.ready_label.configure(text="可以生成")
            self.step_var.set("第 1 步：文件已就绪")
        else:
            self.ready_label.configure(text="待选择文件")

    def _file_state(self, value: str, suffix: str) -> str:
        if not value:
            return "未选择"
        path = Path(value).expanduser()
        if not path.exists():
            return "找不到"
        if path.suffix.lower() != suffix:
            return "格式需确认"
        return "已选择"

    def _show_error(self, title: str, message: str) -> None:
        self.messagebox.showerror(title, message, parent=self.root)


def create_app(root: Any | None = None) -> CatalogLocalizerApp:
    tk, ttk, filedialog, messagebox, scrolledtext = _load_tk()
    if root is None:
        root = tk.Tk()
    return CatalogLocalizerApp(
        root,
        tk_module=tk,
        ttk_module=ttk,
        filedialog_module=filedialog,
        messagebox_module=messagebox,
        scrolledtext_module=scrolledtext,
    )


def _run_demo_from_args(out_dir: Path) -> None:
    with demo_resource_paths() as (segments_path, glossary_path):
        result = run_desktop_workflow(segments_path, glossary_path, out_dir)
    print(result.qa_summary)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--demo-out",
        type=Path,
        help="Run the bundled demo without opening the GUI. Used for package smoke tests.",
    )
    args = parser.parse_args(argv)
    if args.demo_out:
        _run_demo_from_args(args.demo_out)
        return

    app = create_app()
    app.root.mainloop()


if __name__ == "__main__":
    main()
