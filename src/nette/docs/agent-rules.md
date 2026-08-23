## Readability checks with nette

After editing Python files, run the readability check on what changed:

```bash
nette check --diff --format agent
```

Read the exit code first.

- `0`: nothing to fix, move on.
- `1`: findings. Each one carries an `instruction` field naming the file,
  the line and the fix direction. Apply them, then run the check again
  until it exits 0.
- `2`: nette itself could not run (bad path, bad configuration). Read
  stderr and fix the cause. Never ignore a 2.

Do not silence a finding to make the check pass. When a finding is
genuinely wrong for a case, suppress it explicitly, with a reason:

```python
# nette: allow(function-length) generated parser table, edited upstream
```

A suppression without a reason is itself a finding, and a suppression that
silences nothing is reported too, so a stale one cannot hide.

`nette explain RULE` prints the long-form documentation of any rule named
in a finding.
