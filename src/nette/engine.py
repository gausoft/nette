from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Sequence

from nette.calibration import Profile
from nette.cache import Cache, config_key
from nette.findings import Finding
from nette.parsing import parse_source
from nette.rules.base import Context, Rule
from nette.suppressions import apply_allows


def check_files(
    files: Iterable[Path],
    *,
    rules: Sequence[Rule],
    thresholds: dict[str, int] | None = None,
    profile: Profile | None = None,
    cache: Cache | None = None,
    framework: str | None = None,
    silenced: frozenset[str] = frozenset(),
) -> list[Finding]:
    key = (
        config_key(thresholds, [rule.code for rule in rules], profile, framework)
        if cache
        else ""
    )
    findings: list[Finding] = []

    for file in files:
        cached = cache.get(file, key) if cache else None
        if cached is not None:
            findings.extend(cached)
            continue

        fresh = _check_one(file, rules, thresholds, profile, framework)
        if cache:
            cache.put(file, key, fresh)
        findings.extend(fresh)

    return sorted(f for f in findings if f.code not in silenced)


def _check_one(
    file: Path,
    rules: Sequence[Rule],
    thresholds: dict[str, int] | None,
    profile: Profile | None,
    framework: str | None = None,
) -> list[Finding]:
    source = parse_source(file)
    if source.tree is None:
        return list(source.errors)

    contexts = [
        (rule, Context(source, rule, thresholds, profile, framework)) for rule in rules
    ]

    for node in ast.walk(source.tree):
        handler_name = f"visit_{type(node).__name__.lower()}"
        for rule, ctx in contexts:
            handler = getattr(rule, handler_name, None)
            if handler is not None:
                handler(node, ctx)

    findings = [finding for _, ctx in contexts for finding in ctx.findings]

    return apply_allows(
        findings,
        source,
        file_scoped=frozenset(r.code for r in rules if r.scope == "file"),
        active=frozenset(r.code for r in rules if _can_fire(r, profile)),
    )


def _can_fire(rule: Rule, profile: Profile | None) -> bool:
    if not rule.baseline:
        return True

    return profile is not None and rule.baseline in profile.metrics
