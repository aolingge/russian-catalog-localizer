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

    packaged_preview = ", ".join(packaged_files[:4]) if packaged_files else "无"
    if len(packaged_files) > 4:
        packaged_preview = f"{packaged_preview}, ..."

    return "\n".join(
        [
            "QA 摘要",
            f"- 分段总数: {segment_count}",
            f"- 残留中文: {residual_cjk_count}",
            f"- 打包文件数: {len(packaged_files)}",
            f"- 发布包: {package_path.name}",
            f"- 包内预览: {packaged_preview}",
            "",
            *important_lines,
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


def open_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])


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
        self.output_dir_var = self.tk.StringVar(value=str(Path.cwd() / "desktop-output"))
        self.status_var = self.tk.StringVar(value="准备就绪")
        self._busy = False
        self._last_result: WorkflowResult | None = None

        self.root.title("俄文目录本地化工具")
        self.root.geometry("860x620")
        self.root.minsize(760, 520)
        self._build_layout()

    def _build_layout(self) -> None:
        root_frame = self.ttk.Frame(self.root, padding=16)
        root_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(2, weight=1)

        title = self.ttk.Label(root_frame, text="俄文目录本地化工具", font=("", 18, "bold"))
        title.grid(row=0, column=0, sticky="w")
        subtitle = self.ttk.Label(
            root_frame,
            text=(
                "选择 OCR JSON、术语表 CSV 和输出目录后，"
                "一键生成俄文分段、重绘计划、QA 报告和发布包。"
            ),
        )
        subtitle.grid(row=1, column=0, sticky="ew", pady=(4, 14))

        fields = self.ttk.LabelFrame(root_frame, text="输入与输出", padding=12)
        fields.grid(row=2, column=0, sticky="nsew")
        fields.columnconfigure(1, weight=1)
        fields.rowconfigure(3, weight=1)

        self._add_path_row(
            fields,
            row=0,
            label="OCR JSON",
            variable=self.ocr_json_var,
            command=self._choose_ocr_json,
        )
        self._add_path_row(
            fields,
            row=1,
            label="术语表 CSV",
            variable=self.glossary_csv_var,
            command=self._choose_glossary_csv,
        )
        self._add_path_row(
            fields,
            row=2,
            label="输出目录",
            variable=self.output_dir_var,
            command=self._choose_output_dir,
        )

        summary_frame = self.ttk.LabelFrame(fields, text="QA 摘要", padding=8)
        summary_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        self.summary_text = self.scrolledtext.ScrolledText(
            summary_frame,
            height=12,
            wrap=self.tk.WORD,
            state="disabled",
        )
        self.summary_text.grid(row=0, column=0, sticky="nsew")

        actions = self.ttk.Frame(root_frame)
        actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        actions.columnconfigure(4, weight=1)

        self.run_button = self.ttk.Button(
            actions,
            text="运行 Workflow",
            command=self._run_from_form,
        )
        self.run_button.grid(row=0, column=0, padx=(0, 8))
        self.demo_button = self.ttk.Button(actions, text="运行示例 Demo", command=self._run_demo)
        self.demo_button.grid(row=0, column=1, padx=(0, 8))
        self.open_button = self.ttk.Button(
            actions,
            text="打开输出目录",
            command=self._open_output_dir,
        )
        self.open_button.grid(row=0, column=2, padx=(0, 8))
        self.clear_button = self.ttk.Button(actions, text="清空摘要", command=self._clear_summary)
        self.clear_button.grid(row=0, column=3, padx=(0, 8))
        status = self.ttk.Label(actions, textvariable=self.status_var, anchor="e")
        status.grid(row=0, column=4, sticky="ew")

    def _add_path_row(
        self,
        parent: Any,
        *,
        row: int,
        label: str,
        variable: Any,
        command: Callable[[], None],
    ) -> None:
        self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = self.ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 8), pady=4)
        self.ttk.Button(parent, text="选择", command=command).grid(row=row, column=2, pady=4)

    def _choose_ocr_json(self) -> None:
        path = self.filedialog.askopenfilename(
            title="选择 OCR JSON",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self.ocr_json_var.set(path)

    def _choose_glossary_csv(self) -> None:
        path = self.filedialog.askopenfilename(
            title="选择术语表 CSV",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if path:
            self.glossary_csv_var.set(path)

    def _choose_output_dir(self) -> None:
        path = self.filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def _run_from_form(self) -> None:
        segments_value = self.ocr_json_var.get().strip()
        glossary_value = self.glossary_csv_var.get().strip()
        output_value = self.output_dir_var.get().strip()

        if not segments_value:
            self._show_error("缺少 OCR JSON", "请选择 OCR JSON 文件。")
            return
        segments_path = Path(segments_value).expanduser()
        if not segments_path.is_file():
            self._show_error("OCR JSON 不存在", f"找不到文件：\n{segments_path}")
            return
        if not glossary_value:
            self._show_error("缺少术语表 CSV", "请选择术语表 CSV 文件。")
            return
        glossary_path = Path(glossary_value).expanduser()
        if not glossary_path.is_file():
            self._show_error("术语表 CSV 不存在", f"找不到文件：\n{glossary_path}")
            return
        if not output_value:
            self._show_error("缺少输出目录", "请选择输出目录。")
            return
        output_dir = Path(output_value).expanduser()

        self._start_worker(
            "正在运行 workflow...",
            lambda: run_desktop_workflow(segments_path, glossary_path, output_dir),
        )

    def _run_demo(self) -> None:
        output_dir = Path(self.output_dir_var.get() or (Path.cwd() / "demo-output")).expanduser()
        self.output_dir_var.set(str(output_dir))

        def task() -> WorkflowResult:
            with demo_resource_paths() as (segments_path, glossary_path):
                return run_desktop_workflow(segments_path, glossary_path, output_dir)

        self._start_worker("正在运行示例 demo...", task)

    def _start_worker(self, status: str, task: Callable[[], WorkflowResult]) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self.status_var.set(status)
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
        self.status_var.set(f"完成：{result.output_dir}")
        self._write_summary(
            "\n".join(
                [
                    result.qa_summary,
                    "",
                    "输出文件",
                    f"- {result.segments_path}",
                    f"- {result.repaint_plan_path}",
                    f"- {result.qa_report_path}",
                    f"- {result.package_path}",
                ]
            )
        )

    def _on_worker_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("运行失败")
        self._write_summary(f"运行失败：{exc}")
        self._show_error("运行失败", str(exc))

    def _open_output_dir(self) -> None:
        try:
            open_directory(Path(self.output_dir_var.get()).expanduser())
        except Exception as exc:  # pragma: no cover - depends on desktop integration.
            self._show_error("无法打开输出目录", str(exc))

    def _clear_summary(self) -> None:
        self.status_var.set("准备就绪")
        self._write_summary("")

    def _write_summary(self, text: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", self.tk.END)
        if text:
            self.summary_text.insert(self.tk.END, text)
        self.summary_text.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for button in (self.run_button, self.demo_button, self.open_button, self.clear_button):
            button.configure(state=state)

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
