import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Callable, Final, Sequence

from nette import __version__
from nette.cache import Cache
from nette.calibration import Profile, build_profile, load_profile, ratchet, save_profile
from nette.config import KNOWN_FORMATS, find_root, load_config
from nette.discovery import discover
from nette.engine import check_files
from nette.findings import Severity
from nette.gitdiff import changed_files
from nette.output import render
from nette.rules import ALL_RULES, ENGINE_CODES
from nette.suppressions import list_allows

PROFILE_PATH = Path(".nette/profile.json")
CACHE_PATH = Path(".nette/cache")
RULE_DOCS = {
    "parse-error": "engine.md",
    "bare-allow": "engine.md",
    "unused-allow": "engine.md",
    "function-length": "shape.md",
    "branch-density": "shape.md",
    "nesting-depth": "shape.md",
    "argument-count": "shape.md",
    "return-count": "shape.md",
    "short-name-long-scope": "naming.md",
    "naming-drift": "naming.md",
    "over-guarded": "defensiveness.md",
    "under-annotated": "annotations.md",
    "file-naming": "structure.md",
    "file-size": "structure.md",
    "mixed-module": "structure.md",
    "duplicated-sibling": "duplication.md",
}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        return COMMANDS[args.command](args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nette")
    parser.add_argument("--version", action="version", version=f"nette {__version__}")
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
    check.add_argument(
        "--format",
        dest="format",
        default=None,
        choices=sorted(KNOWN_FORMATS),
        metavar="FORMAT",
        help=f"output format: {', '.join(sorted(KNOWN_FORMATS))}",
    )
    check.add_argument(
        "--profile",
        dest="profile_path",
        default=None,
        type=Path,
        help="profile file to judge against (default: .nette/profile.json at the project root)",
    )
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
    calibrate.add_argument(
        "--reset",
        action="store_true",
        help="accept a looser profile than the current one (drops the ratchet)",
    )

    init = commands.add_parser(
        "init", help="set this repo up: profile, ignored cache, agent instructions"
    )
    init.add_argument("path", nargs="?", default=Path("."), type=Path)

    commands.add_parser(
        "agent-rules", help="print the instructions to paste into AGENTS.md"
    )

    allows = commands.add_parser("allows", help="list every suppression marker")
    allows.add_argument("paths", nargs="*", default=[Path(".")], type=Path)

    explain = commands.add_parser("explain", help="print the long-form doc of a rule")
    explain.add_argument("code", metavar="RULE", help="rule name, as printed in findings")

    return parser.parse_args(argv)


def _run_check(args: argparse.Namespace) -> int:
    paths = args.paths or [Path(".")]
    root = _single_root(paths)
    config = load_config(root)
    profile = _profile(args.profile_path, root)

    if args.diff is not None:
        files = changed_files(root, ref=args.diff)
    else:
        files = discover(paths)

    rules = [rule() for rule in ALL_RULES if config.rule_enabled(rule.code, rule.family)]
    silenced = frozenset(
        code for code in ENGINE_CODES if not config.rule_enabled(code, "engine")
    )
    cache = None if args.no_cache or args.timings else Cache(root / CACHE_PATH)

    findings = check_files(
        files,
        rules=rules,
        thresholds=config.thresholds,
        profile=profile,
        cache=cache,
        framework=config.framework,
        silenced=silenced,
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


def _single_root(paths: Sequence[Path]) -> Path:
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise ValueError(f"no such path: {', '.join(str(path) for path in missing)}")

    roots = {find_root([path]) for path in paths}
    if len(roots) > 1:
        named = ", ".join(sorted(str(root) for root in roots))
        raise ValueError(
            f"the paths given belong to different projects ({named}); "
            "check one project at a time"
        )

    return roots.pop()


def _profile(override: Path | None, root: Path) -> Profile | None:
    if override is None:
        return load_profile(root / PROFILE_PATH)

    if not override.exists():
        raise ValueError(f"no such profile file: {override}")

    return load_profile(override)


def _run_calibrate(args: argparse.Namespace) -> int:
    measured = build_profile(_existing(args.path))
    destination = find_root([args.path]) / PROFILE_PATH
    previous = None if args.reset else load_profile(destination)

    profile = measured if previous is None else ratchet(previous, measured)
    loosened = [name for name, value in measured.metrics.items() if profile.metrics[name] != value]

    save_profile(profile, destination)
    print(f"profile written to {destination} ({profile.files_measured} files measured)")
    if loosened:
        print(f"kept the stricter baseline for {', '.join(sorted(loosened))} (--reset to relax)")

    return 0


def _run_init(args: argparse.Namespace) -> int:
    root = find_root([_existing(args.path)])
    profile_path = root / PROFILE_PATH

    if profile_path.exists():
        print(f"profile already at {profile_path}, keeping it")
    else:
        profile = build_profile(args.path)
        save_profile(profile, profile_path)
        print(
            f"profile written to {profile_path} "
            f"({profile.files_measured} files measured), commit it"
        )

    _ignore_cache(root)

    print("\nnext: check the tree with `nette check`, or only what changed with")
    print("`nette check --diff`. To teach your agent the loop, run:\n")
    print("    nette agent-rules >> AGENTS.md")

    return 0


def _ignore_cache(root: Path) -> None:
    ignore = root / CACHE_PATH.parent / ".gitignore"
    pattern = f"{CACHE_PATH.name}/"
    previous = ignore.read_text(encoding="utf-8") if ignore.exists() else ""

    if pattern in previous.split():
        return

    separator = "" if not previous or previous.endswith("\n") else "\n"
    ignore.parent.mkdir(parents=True, exist_ok=True)
    ignore.write_text(f"{previous}{separator}{pattern}\n", encoding="utf-8")
    print(f"{ignore} keeps the result cache out of git")


def _existing(path: Path) -> Path:
    if not path.exists():
        raise ValueError(f"no such path: {path}")

    return path


def _run_agent_rules(_: argparse.Namespace) -> int:
    print(_doc("agent-rules.md"))

    return 0


def _run_allows(args: argparse.Namespace) -> int:
    files = discover(args.paths)

    for allow in list_allows(files):
        reason = allow.reason or "(no reason)"
        print(f"{allow.file} {allow.line} allow({allow.code}) {reason}")

    return 0


def _run_explain(args: argparse.Namespace) -> int:
    doc_file = RULE_DOCS.get(args.code)
    if doc_file is None:
        print(
            f"unknown rule {args.code}; known: {', '.join(sorted(RULE_DOCS))}",
            file=sys.stderr,
        )
        return 2

    text = _doc(doc_file)
    print(_extract_section(text, args.code))

    return 0


def _doc(name: str) -> str:
    return (Path(__file__).parent / "docs" / name).read_text(encoding="utf-8").rstrip()


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


COMMANDS: Final[dict[str, Callable[[argparse.Namespace], int]]] = {
    "check": _run_check,
    "init": _run_init,
    "agent-rules": _run_agent_rules,
    "calibrate": _run_calibrate,
    "allows": _run_allows,
    "explain": _run_explain,
}


if __name__ == "__main__":
    sys.exit(main())
