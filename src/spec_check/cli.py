"""Command-line entry point: spec-check [PATH] [--strict] [--json] [-o FILE]."""

from __future__ import annotations

import argparse
import sys

from .report import exit_code, render_json, render_markdown
from .run import check


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spec-check",
        description=(
            "Mechanizes specs/checking.md: reads specs, checks for conflicts, "
            "gaps, dead rules, unknown terms, and staleness, and emits a "
            "REPORT.md-style report. Read-only (CHK-R7)."
        ),
    )
    p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="repo root containing specs/ (default: current directory)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="promote warnings to errors (affects exit code only)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="emit findings as structured JSON instead of markdown",
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write the report to FILE instead of stdout",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check(args.path)

    if args.json:
        text = render_json(result)
    else:
        text = render_markdown(result, strict=args.strict)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
            if not text.endswith("\n"):
                fh.write("\n")
    else:
        print(text)

    return exit_code(result, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
