# openmd

`openmd` is a small Bash CLI that turns a Markdown file into a polished local HTML preview.

It keeps the input file untouched, writes a temporary `.html` file, and opens it in your browser unless you tell it not to.

## Features

- GitHub-flavored Markdown rendering
- Syntax highlighting for fenced code blocks
- Light, dark, and system theme modes
- Sticky header with source path and generation time
- Stable in-page heading anchors
- Quick actions to save as PDF, copy the Markdown, or copy the file path
- `--no-open` and `OPENMD_NO_OPEN=1` support for CI or non-interactive use

## Requirements

- `bash`
- `python3`
- A browser launcher such as `open`, `xdg-open`, or `start` if you want automatic opening
- Network access in the browser for the CDN-hosted CSS and JavaScript assets

## Usage

```bash
./openmd [options] <markdown-file>
```

### Options

- `--title TEXT`: set a custom HTML `<title>`
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

That file is a standalone local preview page containing the rendered Markdown plus the UI controls.

## Notes

- The generated preview reflects the file contents at generation time. Reloading the page does not re-read the source file.
- The preview uses CDN assets for Marked, highlight.js, and GitHub Markdown CSS. If those are unavailable, Markdown rendering falls back to a plain escaped `<pre>` block.
- `.html` files are ignored by this repository's `.gitignore`.
