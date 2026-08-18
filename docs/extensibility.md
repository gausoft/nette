# Extensibility Design: Three Tiers

A lesson from ecosystem history: extensibility decides adoption. ESLint won
on plugins. Biome and Oxlint are 50x faster and still can't displace it.
ruff has kept its plugin issue open since 2022, structurally blocked by its
Rust core.

nette is pure Python: users extend it in the language they already know.

## Tier 1: Declarative config (TOML), ~80% of needs

Enable and disable rules, tune thresholds. Zero code.

```toml
[tool.nette]
ignore = ["N201"]

[tool.nette.thresholds]
statements_per_function = 30
```

## Tier 2: Pattern rules (YAML), ~15% of needs

The semgrep/ast-grep model: a pattern that looks like the code it matches,
plus metavariables. Easy to write, easy to share.

```yaml
- id: no-defensive-getattr
  pattern: getattr($OBJ, $ATTR, $DEFAULT)
  message: "Direct attribute access on internal models; getattr only on external SOAP/external API responses."
  severity: warning
```

Strictly declarative: no shell commands, no arbitrary code execution (a
security lesson from ast-grep's `custom` transformer debate).

Shareable rule packs (e.g. `nette-rules-fastapi`) are the community
flywheel. Semgrep built a registry of over 20,000 rules on this model.

## Tier 3: Python rules (plugin API), ~5% of needs

The ESLint model: a class with `visit_<node>` methods, receiving the AST and
repo context (call graph, sibling files, calibration data). Made for deep
org-specific rules, the exact demand ruff has been unable to serve.

```python
from nette import Rule, Context

class NoBusinessLogicInEndpoints(Rule):
    id = "ORG001"

    def visit_function(self, node, ctx: Context):
        ...
```

**Dogfooding guarantee:** every built-in nette rule uses this same public
API. If the API can't express a rule we need, we fix the API.

## Cross-tier invariants

1. **One AST.** All three tiers see the same parse tree, never two parsers
   (the trap ruff avoided by rejecting the ast-grep integration).
2. **Explicit opt-in.** Installing a package never silently activates rules
   (flake8's mistake). Everything is declared in config.
3. **Per-rule timing.** `nette check --timings` shows the cost of every rule,
   built-in or custom. Slow rules are visible, always.
4. **Single config surface.** One file, one mechanism. No maze of plugins vs
   extends vs presets (ESLint's mistake).
