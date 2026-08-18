# Architecture invariants

Design rules that hold across the whole engine. Question them in
decisions.md before breaking them.

## Core

1. **One AST.** Every rule tier (TOML thresholds, YAML patterns, Python
   plugins) sees the same parse tree. Never two parsers.
2. **Deterministic runtime.** Same code in, same verdict out. No LLM, no
   network call, no randomness in the check path.
3. **Diff-first.** The default unit of judgment is the change, not the
   repository. Whole-repo analysis exists for calibration and audit.
4. **Sub-second verdict.** Performance is a feature. Design for caching,
   incremental analysis and parallelism from the start.

## Extensibility

5. **Explicit opt-in.** Installing a package never silently activates
   rules. Everything is declared in config.
6. **Per-rule timing.** The cost of every rule, built-in or custom, is
   measurable and visible (`--timings`).
7. **Declarative tier stays declarative.** YAML rules cannot execute
   arbitrary code or shell commands.
8. **Dogfooding.** Built-in rules use the same public API as third-party
   Python rules. If the API cannot express a rule we need, fix the API.

## Output

9. **Actionable findings.** A finding names the problem, the location and
   the concrete fix direction. Numbers alone are not findings.
10. **Agent-consumable output.** Structured output (JSON) is a first-class
    citizen, not an afterthought.
