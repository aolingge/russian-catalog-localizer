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


def _run_packaged_demo(out_dir: Path) -> None:
    """Run the desktop smoke path without opening the GUI."""
    with demo_resource_paths() as (segments_path, glossary_path):
        result = run_desktop_workflow(segments_path, glossary_path, out_dir)

    print(result.qa_summary)
    print(f"Wrote {result.segments_path}")
    print(f"Wrote {result.repaint_plan_path}")
    print(f"Wrote {result.qa_report_path}")
    print(f"Wrote {result.package_path}")


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--demo-out", type=Path)
    args, _ = parser.parse_known_args(argv)

    if args.demo_out:
        _run_packaged_demo(args.demo_out)
        return

    desktop_main(argv)


if __name__ == "__main__":
    main()
