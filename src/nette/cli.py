import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

from nette.cache import Cache
from nette.calibration import build_profile, load_profile, save_profile
from nette.config import load_config
from nette.discovery import discover
from nette.engine import check_files
from nette.findings import Severity
from nette.gitdiff import changed_files
from nette.output import render
from nette.rules.defensiveness import Defensiveness
from nette.rules.shape import SHAPE_RULES
from nette.suppressions import list_allows

PROFILE_PATH = Path(".nette/profile.json")
CACHE_PATH = Path(".nette/cache")
ALL_RULES = (*SHAPE_RULES, Defensiveness)
RULE_DOCS = {
    "NET000": ("engine.md", "parse-error"),
    "NET001": ("engine.md", "bare-allow"),
    "NET101": ("shape.md", "function-length"),
    "NET102": ("shape.md", "nesting-depth"),
    "NET103": ("shape.md", "argument-count"),
    "NET104": ("shape.md", "return-count"),
    "NET301": ("defensiveness.md", "over-guarded"),
}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.command == "check":
        return _run_check(args)
    if args.command == "allows":
        return _run_allows(args)
    if args.command == "explain":
        return _run_explain(args)
    return _run_calibrate(args)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nette")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="check files for readability findings")
    check.add_argument("paths", nargs="*", type=Path)
    check.add_argument(
        "--diff",
        nargs="?",
        const="HEAD",
        default=None,
        metavar="REF",
        help="check only files changed since REF (default: HEAD)",
    )
    check.add_argument("--format", dest="format", default=None)
    check.add_argument("--no-cache", action="store_true")
    check.add_argument("--timings", action="store_true")
    check.add_argument(
        "--fail-on",
        choices=["any", "error"],
        default="any",
        help="exit 1 on any finding (default) or only on error-severity findings",
    )

    calibrate = commands.add_parser("calibrate", help="measure the repo style profile")
    calibrate.add_argument("path", nargs="?", default=Path("."), type=Path)

    allows = commands.add_parser("allows", help="list every suppression marker")
    allows.add_argument("paths", nargs="*", default=[Path(".")], type=Path)

    explain = commands.add_parser("explain", help="print the long-form doc of a rule")
    explain.add_argument("code")

    return parser.parse_args(argv)


def _run_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    config = load_config(root)

    if args.diff is not None:
        files = changed_files(root, ref=args.diff)
    elif args.paths:
        files = discover(args.paths)
    else:
        print("error: give paths to check, or --diff", file=sys.stderr)
        return 2

    rules = [rule() for rule in ALL_RULES if config.rule_enabled(rule.code)]
    profile = load_profile(root / PROFILE_PATH)
    cache = None if args.no_cache or args.timings else Cache(root / CACHE_PATH)

    findings = check_files(
        files,
        rules=rules,
        thresholds=config.thresholds,
        profile=profile,
        cache=cache,
    )

    if args.timings:
        _print_timings(files, rules, config.thresholds, profile)

    output = render(findings, format=args.format or config.output_format)
    if output:
        print(output)

    if args.fail_on == "error":
        failing = [f for f in findings if f.severity is Severity.ERROR]
    else:
        failing = list(findings)

    return 1 if failing else 0


def _run_calibrate(args: argparse.Namespace) -> int:
    profile = build_profile(args.path)
    destination = Path.cwd() / PROFILE_PATH

    save_profile(profile, destination)
    print(f"profile written to {destination} ({profile.files_measured} files measured)")

    return 0


def _run_allows(args: argparse.Namespace) -> int:
    files = discover(args.paths)

    for allow in list_allows(files):
        reason = allow.reason or "(no reason)"
        print(f"{allow.file} {allow.line} allow({allow.code}) {reason}")

    return 0


def _run_explain(args: argparse.Namespace) -> int:
    entry = RULE_DOCS.get(args.code)
    if entry is None:
        known = ", ".join(sorted(RULE_DOCS))
        print(f"unknown rule code {args.code}; known: {known}", file=sys.stderr)
        return 2

    doc_file, section = entry
    text = (Path(__file__).parent / "docs" / doc_file).read_text()
    print(f"{args.code} ({section})\n")
    print(_extract_section(text, section))

    return 0


def _extract_section(text: str, section: str) -> str:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(f"## `{section}`"))
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )

    return "\n".join(lines[start:end]).strip()


def _print_timings(files, rules, thresholds, profile) -> None:
    totals: dict[str, float] = defaultdict(float)

    for rule in rules:
        started = time.perf_counter()
        check_files(files, rules=[rule], thresholds=thresholds, profile=profile)
        totals[rule.code] += time.perf_counter() - started

    for code, seconds in sorted(totals.items(), key=lambda item: -item[1]):
        print(f"{code} {seconds * 1000:.1f} ms", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
