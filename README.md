# openmd

`openmd` is a small Bash CLI that turns a Markdown file into a polished local HTML preview.

It keeps the input file untouched, writes a temporary `.html` file, and opens it in your browser unless you tell it not to.

## Features

- GitHub-flavored Markdown rendering
- Syntax highlighting for fenced code blocks
- Light, dark, and system theme modes
- Sticky header with source path and generation time
- Local links and images resolved from the Markdown file’s directory, including raw HTML `<img src>` and `srcset`
- Git status and a selector for the working copy, HEAD, and local branches
- Stable in-page heading anchors
- Quick actions to save as PDF, copy the Markdown, or copy the file path
- `--no-open` and `OPENMD_NO_OPEN=1` support for CI or non-interactive use

## Requirements

- `bash`
- `python3`
- `git` (optional, enables version selection for tracked files)
- A browser launcher such as `open`, `xdg-open`, or `start` if you want automatic opening
- Network access in the browser for the CDN-hosted CSS and JavaScript assets

## Usage

```bash
./openmd [options] <markdown-file>
```

### Options

- `--title TEXT`: set a custom HTML `<title>`
- `--version`: print the installed version
- `--no-open`: generate the preview without launching a browser
- `-h`, `--help`: print usage information

### Environment

- `OPENMD_NO_OPEN=1`: skip opening the generated preview
- `OPENMD_OUTPUT_DIR=/path/to/dir`: choose where the temporary HTML file is written

## Examples

Preview a file and open it in your browser:

```bash
./openmd notes/today.md
```

Generate a preview without launching a browser:

```bash
./openmd --no-open docs/spec.md
```

Set a custom page title:

```bash
./openmd --title "Release Notes Preview" CHANGELOG.md
```

Write the generated preview into a specific directory:

```bash
OPENMD_OUTPUT_DIR="$PWD/tmp" ./openmd docs/architecture.md
```

Use it in CI or scripts without opening a browser:

```bash
OPENMD_NO_OPEN=1 ./openmd README.md
```

## Output

`openmd` prints the path to the generated HTML file:

```text
openmd: wrote /tmp/openmd.ABC123.html
```

That file is a local preview page containing the Markdown and UI controls. Open the generated `.html` file directly in your browser; keep the original source directory available for local links and images.

## Local links and images

Relative paths are resolved from the directory containing the input Markdown, even when the preview is written elsewhere. For example, with `docs/report.md`:

```markdown
[Download the data](../data/results.csv)
![Chart](images/chart.png)
<img src="images/chart.png" alt="Chart">
```

These point to `data/results.csv` and `docs/images/chart.png`, respectively. Spaces and Unicode in the source directory are supported; use URL encoding for special characters in link destinations (for example, `results%20final.csv` or `chart%23one.png`). In-page links such as `[Results](#results)` stay in the preview. Absolute URLs keep their usual meaning.

Linked files open or download according to your browser’s handling of their file type; CSV files are not converted into HTML tables. Linked Markdown files are opened as source files; run `openmd` on them for a rendered preview.

## Git versions

For a Git-tracked input file, the header shows:

- The current branch, or the commit when HEAD is detached.
- Repository status, distinguishing staged changes, unstaged changes, and untracked files.
- Status for the input file itself.
- A **View** selector, defaulting to **Working copy** (the file on disk, including uncommitted edits).

Choose **Last committed version (HEAD)** to view the file at the current commit, or **Branch: <name>** to view it at a local branch’s tip. This does not check out a branch or modify the repository. Branches where the same file path is absent are shown as unavailable; renames across branches are not followed. Remote branches are not fetched or listed. **Copy Markdown** copies the selected version. Switching **View** returns to the top of the page and clears the previous section anchor.

Links and images in every version resolve against the current source directory. Only the Markdown is versioned in the preview: historical attachments are not extracted from Git, so an asset that exists only on another branch will be unavailable.

All versions and status indicators are captured when you run `openmd`. Run it again to refresh them. Files outside Git, untracked input files, and systems without Git still get the normal preview. A newly staged file in a repository with no commits gets working-copy status without a committed version.

## Notes

- The generated preview reflects the file contents at generation time. Reloading the page does not re-read the source file.
- The preview uses CDN assets for Marked, highlight.js, and GitHub Markdown CSS. If those are unavailable, Markdown rendering falls back to a plain escaped `<pre>` block.
- `.html` files are ignored by this repository's `.gitignore`.

## Downloads and releases

Download the executable or archive from [GitHub Releases](https://github.com/someone-in-texas/openmd/releases). The executable works on macOS and Linux with the requirements above; after downloading, run `chmod +x openmd` and `./openmd --version`. Each release includes `SHA256SUMS` for verifying downloads (`shasum -a 256 -c SHA256SUMS` on macOS, or `sha256sum -c SHA256SUMS` on Linux, with all assets downloaded).

See [RELEASE.md](RELEASE.md) for the tested release process and [CHANGELOG.md](CHANGELOG.md) for changes.
