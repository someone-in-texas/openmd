#!/usr/bin/env bash
# Install the executable from a checksum-verified GitHub release.
set -euo pipefail

main() {
  version="${OPENMD_VERSION:-0.5.1}"
  version="${version#v}"
  install_dir="${OPENMD_INSTALL_DIR:-$HOME/.local/bin}"
  if [[ "${1:-}" == '--help' ]]; then
    cat <<'HELP'
Usage: bash install.sh
Installs openmd to ~/.local/bin without sudo.
OPENMD_INSTALL_DIR=/path  Choose the installation directory.
OPENMD_VERSION=0.5.1      Choose a release (an optional v prefix is accepted).
Requires Bash, Python 3, and curl. Downloads and verifies SHA256SUMS before installing.
HELP
    return
  fi
  if [[ $# -ne 0 || ! "$version" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
    printf 'openmd installer: invalid arguments or OPENMD_VERSION\n' >&2
    return 1
  fi
  for dependency in python3 curl; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
      printf 'openmd installer: required command %s not found\n' "$dependency" >&2
      return 1
    fi
  done
  temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/openmd-install.XXXXXX")
  staged_path=''
  trap 'rm -rf "$temp_dir"; if [[ -n "$staged_path" ]]; then rm -f "$staged_path"; fi' EXIT
  release_url="https://github.com/someone-in-texas/openmd/releases/download/v$version"
  for asset in openmd SHA256SUMS; do
    curl --proto '=https' --proto-redir '=https' --tlsv1.2 --fail --silent --show-error --location --retry 3 \
      "$release_url/$asset" -o "$temp_dir/$asset"
  done
  python3 - "$temp_dir" <<'PY'
import hashlib
from pathlib import Path
import sys
root = Path(sys.argv[1])
checksums = [line.split() for line in (root / 'SHA256SUMS').read_text().splitlines()]
expected = [parts[0] for parts in checksums if len(parts) == 2 and parts[1] == 'openmd']
actual = hashlib.sha256((root / 'openmd').read_bytes()).hexdigest()
if expected != [actual]:
    sys.exit('openmd installer: checksum verification failed; existing installation unchanged')
PY
  bash -n "$temp_dir/openmd"
  if [[ "$(bash "$temp_dir/openmd" --version)" != "openmd $version" ]]; then
    printf 'openmd installer: downloaded executable has the wrong version\n' >&2
    return 1
  fi
  mkdir -p "$install_dir"
  if [[ -d "$install_dir/openmd" ]]; then
    printf 'openmd installer: destination is a directory: %s/openmd\n' "$install_dir" >&2
    return 1
  fi
  # Stage on the destination filesystem so replacing an existing install is atomic.
  staged_path=$(mktemp "$install_dir/.openmd.XXXXXX")
  cp "$temp_dir/openmd" "$staged_path"
  chmod 755 "$staged_path"
  mv -f "$staged_path" "$install_dir/openmd"
  staged_path=''
  printf 'Installed openmd %s to %s/openmd\n' "$version" "$install_dir"
  case ":$PATH:" in
    *":$install_dir:"*) ;;
    *) printf 'Add this directory to your PATH: %s\n' "$install_dir" ;;
  esac
}

main "$@"
