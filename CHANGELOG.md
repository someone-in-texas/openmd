# Changelog

## 0.5.1

- Add a curl installer at the top of the README, available as a release download.
- Install to `~/.local/bin` or a custom directory, with optional version selection.
- Verify SHA-256 and executable version before atomically replacing an installation.
- Test successful installs, upgrades, and failed downloads/checksums on Linux and macOS; verify the public curl install after release publication.

## 0.5

- Resolve local links and images relative to the Markdown source, including CSV downloads and raw HTML images.
- Show Git branch, staged/unstaged changes, and untracked-file status.
- Select the working copy, HEAD, or another local branch without checking out files.
- Return to the top when switching views, clearing stale section anchors.
- Preserve section links, selected-version copying, themes, and the offline fallback.
- Add `--version`, automated smoke/browser checks, and GitHub release downloads with SHA-256 checksums.
