from __future__ import annotations

import argparse
import sys
from pathlib import Path

from russian_catalog_localizer.desktop_app import (
    demo_resource_paths,
    run_desktop_workflow,
)
from russian_catalog_localizer.desktop_app import (
    main as desktop_main,
)


def _run_tk_smoke() -> None:
    """Verify that the packaged Tcl/Tk runtime can create a hidden root window."""
    import tkinter as tk

    root = tk.Tk()
    try:
        root.withdraw()
        root.update_idletasks()
    finally:
        root.destroy()
    print("Tk smoke: passed")


def _run_packaged_demo(out_dir: Path) -> None:
    """Run the desktop smoke path without opening the GUI."""
    with demo_resource_paths() as (segments_path, glossary_path):
        result = run_desktop_workflow(segments_path, glossary_path, out_dir)

    print("Demo smoke: passed")
    print(f"Segments checked: {result.segment_count}")
    print(f"Residual Chinese hits: {result.residual_cjk_count}")
    print(f"Packaged files: {', '.join(result.packaged_files)}")
    print(f"Wrote {result.segments_path.name}")
    print(f"Wrote {result.repaint_plan_path.name}")
    print(f"Wrote {result.qa_report_path.name}")
    print(f"Wrote {result.package_path.name}")


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--demo-out", type=Path)
    parser.add_argument("--tk-smoke", action="store_true")
    args, _ = parser.parse_known_args(argv)

    if args.tk_smoke:
        _run_tk_smoke()
        return

    if args.demo_out:
        _run_packaged_demo(args.demo_out)
        return

    desktop_main(argv)


if __name__ == "__main__":
    main()
