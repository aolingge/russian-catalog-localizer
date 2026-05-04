from __future__ import annotations

import argparse
from importlib.resources import as_file, files
from pathlib import Path

from .glossary import load_glossary, localize_segments
from .ocr import load_segments, normalize_segments, write_segments
from .packager import pack_directory
from .qa import write_report
from .renderer import write_repaint_plan


def run_workflow(segments_path: Path, glossary_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    segments = normalize_segments(load_segments(segments_path))
    glossary = load_glossary(glossary_path)
    localized = localize_segments(segments, glossary)

    localized_path = out_dir / "segments.ru.json"
    repaint_path = out_dir / "repaint_plan.json"
    qa_path = out_dir / "qa_report.md"
    package_path = out_dir / "localized_package.zip"

    write_segments(localized_path, localized, source="localized")
    write_repaint_plan(repaint_path, localized)
    write_report(qa_path, localized)
    added = pack_directory(out_dir, package_path)

    print(f"Wrote {localized_path}")
    print(f"Wrote {repaint_path}")
    print(f"Wrote {qa_path}")
    print(f"Wrote {package_path} ({len(added)} files)")


def cmd_demo(args: argparse.Namespace) -> None:
    example_dir = files("russian_catalog_localizer").joinpath("examples")
    with (
        as_file(example_dir.joinpath("sample_ocr_segments.json")) as segments_path,
        as_file(example_dir.joinpath("glossary.zh-ru.csv")) as glossary_path,
    ):
        run_workflow(segments_path, glossary_path, args.out)


def cmd_ocr(args: argparse.Namespace) -> None:
    if args.input.suffix.lower() != ".json":
        raise SystemExit(
            "No binary OCR backend is bundled. Export OCR segments as JSON first, "
            "or add an adapter that returns russian_catalog_localizer.models.Segment objects."
        )
    segments = normalize_segments(load_segments(args.input))
    write_segments(args.out, segments, source="normalized-ocr-json")
    print(f"Wrote {args.out}")


def cmd_workflow(args: argparse.Namespace) -> None:
    run_workflow(args.segments, args.glossary, args.out)


def cmd_render_plan(args: argparse.Namespace) -> None:
    segments = load_segments(args.segments)
    write_repaint_plan(args.out, segments)
    print(f"Wrote {args.out}")


def cmd_qa(args: argparse.Namespace) -> None:
    segments = load_segments(args.segments)
    write_report(args.out, segments)
    print(f"Wrote {args.out}")


def cmd_pack(args: argparse.Namespace) -> None:
    added = pack_directory(args.source, args.out, max_file_mb=args.max_file_mb)
    print(f"Wrote {args.out} ({len(added)} files)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rcl",
        description="Local-first Chinese to Russian catalog localization skeleton.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the synthetic sample workflow.")
    demo.add_argument("--out", type=Path, default=Path("demo-output"))
    demo.set_defaults(func=cmd_demo)

    ocr = subparsers.add_parser("ocr", help="Normalize an OCR JSON export.")
    ocr.add_argument("--input", type=Path, required=True)
    ocr.add_argument("--out", type=Path, required=True)
    ocr.set_defaults(func=cmd_ocr)

    workflow = subparsers.add_parser("workflow", help="Run localize, repaint plan, QA, and pack.")
    workflow.add_argument("--segments", type=Path, required=True)
    workflow.add_argument("--glossary", type=Path, required=True)
    workflow.add_argument("--out", type=Path, required=True)
    workflow.set_defaults(func=cmd_workflow)

    render_plan = subparsers.add_parser("render-plan", help="Write a renderer-neutral repaint plan.")
    render_plan.add_argument("--segments", type=Path, required=True)
    render_plan.add_argument("--out", type=Path, required=True)
    render_plan.set_defaults(func=cmd_render_plan)

    qa = subparsers.add_parser("qa", help="Write a residual Chinese QA report.")
    qa.add_argument("--segments", type=Path, required=True)
    qa.add_argument("--out", type=Path, required=True)
    qa.set_defaults(func=cmd_qa)

    pack = subparsers.add_parser("pack", help="Package a safe artifact directory.")
    pack.add_argument("--source", type=Path, required=True)
    pack.add_argument("--out", type=Path, required=True)
    pack.add_argument("--max-file-mb", type=float, default=50.0)
    pack.set_defaults(func=cmd_pack)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
