# AGENTS.md

This repository is intentionally small. Treat it like a single-script utility, not a framework.

## Repository Shape

- `openmd`: the entire CLI implementation
- `.gitignore`: currently ignores generated `.html` files
- `README.md`: human-facing usage documentation
- `AGENTS.md`: agent-facing workflow notes

The runtime has no build system or package manager. `tests/` contains standalone Python and Chromium checks. `scripts/package.py` creates release downloads, and `.github/workflows/release.yml` tests changes and publishes tagged releases. See `RELEASE.md` for the release procedure.

## What `openmd` Does

`openmd` reads one Markdown file, generates a temporary HTML preview, and optionally opens it in a browser.

Implementation details:

- CLI and process control are in Bash
- Absolute-path resolution and HTML generation are delegated to `python3`
- The generated page depends on CDN-hosted `marked`, `highlight.js`, and GitHub Markdown CSS
- Theme switching, anchor scrolling, and copy/print actions are implemented inline in the generated HTML/JS

## Working Rules For Agents

- Read `openmd` before editing. Most behavior changes affect both shell flow and embedded HTML/JS.
- Keep the tool dependency-light. New dependencies should be a last resort.
- Preserve the current interface unless the task explicitly requires a breaking change:
  - positional file argument
  - `--title`
  - `--no-open`
  - `OPENMD_NO_OPEN`
  - `OPENMD_OUTPUT_DIR`
- Prefer targeted edits. The project is small enough that broad refactors are usually unnecessary.
- When changing preview behavior, verify both the Bash path and the generated client-side code path.
- If you add a feature, update `usage()` and `README.md` in the same change.

## Validation

Run `python3 tests/smoke.py` for CLI and Git regressions; run `tests/browser.cjs` as documented in `RELEASE.md` for preview changes. Also use these lightweight checks:

```bash
./openmd --help
./openmd --no-open README.md
OPENMD_NO_OPEN=1 ./openmd README.md
OPENMD_OUTPUT_DIR="${TMPDIR:-/tmp}" ./openmd --no-open README.md
```

Check for these outcomes:

- the command exits successfully for valid inputs
- the generated file path is printed
- invalid arguments still fail clearly
- browser launching stays skipped when `--no-open` or `OPENMD_NO_OPEN=1` is set

## Editing Guidance

- Be careful inside the embedded Python and JavaScript blocks. Quoting mistakes will break the CLI.
- Preserve `set -euo pipefail`.
- Preserve the fallback renderer path when CDN assets are unavailable.
- Preserve cross-platform launcher detection order unless there is a concrete reason to change it.
- Avoid introducing shell features that would reduce portability beyond standard Bash usage.

## Common Change Areas

- CLI options: `parse_args()` and `usage()`
- output-file handling: `create_temp_html()`
- browser launching: `launch_browser()`
- preview HTML structure and CSS: the large Python heredoc template
- theme, anchor, and quick-action behavior: inline JavaScript in that template

## Documentation Expectations

- `README.md` is for human users. Keep examples copy-pasteable.
- `AGENTS.md` is for coding tools. Keep it concrete and operational.
