# Rules

Long-form documentation for every nette rule. This is the content served
by `nette explain CODE`.

Codes are stable and never renumbered.

| Range | Family | Threshold kind |
|---|---|---|
| [NET0xx](net0xx-engine.md) | Engine and parse | none |
| [NET1xx](net1xx-shape.md) | Shape: length, nesting, arguments, returns | universal |
| [NET3xx](net3xx-defensiveness.md) | Defensiveness and error handling | calibrated |
| [NET5xx](net5xx-structure.md) | Project structure | mixed |

Two threshold kinds:

- **Universal** rules have a numeric default measured on exemplary
  codebases (httpx, pydantic, fastapi, attrs, curated stdlib), overridable
  under `[tool.nette.thresholds]`.
- **Calibrated** rules have no absolute threshold. They compare the file
  under judgment to the repository's own profile (`.nette/profile.json`,
  built by `nette calibrate`) and fire on deviation from it.

Suppressing a finding: put `# nette: allow(CODE) reason` on the offending
line or the line above. The reason is mandatory. `nette allows` lists
every suppression in the tree.
