# Rules

Long-form documentation for every nette rule. This is the content served
by `nette explain RULE`.

Rule identifiers are speaking slugs: they name the detected problem, so a
finding is understandable without a lookup. A published slug is never
renamed. Rules group into families, which is what `select` takes in
config.

| Family | Rules | Threshold kind |
|---|---|---|
| [engine](engine.md) | `parse-error`, `bare-allow`, `unused-allow` | none |
| [shape](shape.md) | `function-length`, `branch-density`, `nesting-depth`, `argument-count`, `return-count` | universal |
| [naming](naming.md) | `short-name-long-scope`, `naming-drift` | mixed |
| [defensiveness](defensiveness.md) | `over-guarded`, `guard-density` | calibrated |
| [annotations](annotations.md) | `under-annotated` | calibrated |
| [structure](structure.md) | `file-naming`, `file-size`, `mixed-module` | mixed |
| [duplication](duplication.md) | `duplicated-sibling` | convention |
| [local](local.md) | the rules you declare in `.nette/rules.toml` | declared |

Three threshold kinds:

- **Universal** rules have a numeric default measured on exemplary
  codebases (httpx, pydantic, fastapi, attrs, curated stdlib), overridable
  under `[tool.nette.thresholds]`.
- **Calibrated** rules have no absolute threshold. They compare the file
  under judgment to the repository's own profile (`.nette/profile.json`,
  built by `nette calibrate`) and fire on deviation from it.
- **Convention** rules judge a decision the repo makes once and then has
  to keep. They are declared in TOML and never read the profile: learning
  from a repo that already drifted would silence the rule where it is
  needed most. Their defaults are set low enough that exemplary code
  stays quiet.

Suppressing a finding: put `# nette: allow(rule-slug) reason` on the
offending line or the line above. The reason is mandatory. `nette allows`
lists every suppression in the tree.

Third-party plugin rules (v0.2+) are prefixed with their package name:
`org/no-print-in-prod`. Native slugs are never prefixed.
