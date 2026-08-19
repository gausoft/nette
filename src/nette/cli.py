"""Command line interface: nette check, nette calibrate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nette.cache import Cache
from nette.calibration import build_profile, load_profile, save_profile
from nette.config import load_config
from nette.discovery import discover
from nette.engine import check_files
from nette.findings import Severity
from nette.output import render
from nette.rules.defensiveness import Defensiveness
from nette.rules.shape import SHAPE_RULES

PROFILE_PATH = Path(".nette/profile.json")
CACHE_PATH = Path(".nette/cache")
ALL_RULES = (*SHAPE_RULES, Defensiveness)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.command == "check":
        return _run_check(args)
    return _run_calibrate(args)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nette")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="check files for readability findings")
    check.add_argument("paths", nargs="+", type=Path)
    check.add_argument("--format", dest="format", default=None)
    check.add_argument("--no-cache", action="store_true")
    check.add_argument(
        "--fail-on",
        choices=["any", "error"],
        default="any",
        help="exit 1 on any finding (default) or only on error-severity findings",
    )

    calibrate = commands.add_parser("calibrate", help="measure the repo style profile")
    calibrate.add_argument("path", nargs="?", default=Path("."), type=Path)

    return parser.parse_args(argv)


def _run_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    config = load_config(root)

    rules = [rule() for rule in ALL_RULES if config.rule_enabled(rule.code)]
    profile = load_profile(root / PROFILE_PATH)
    cache = None if args.no_cache else Cache(root / CACHE_PATH)

    findings = check_files(
        discover(args.paths),
        rules=rules,
        thresholds=config.thresholds,
        profile=profile,
        cache=cache,
    )

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


if __name__ == "__main__":
    sys.exit(main())
