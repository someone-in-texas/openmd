# Releasing openmd

The runtime stays a single Bash/Python script. The release workflow tests Linux and macOS, runs Chromium regressions, and publishes only when a `v*` tag passes all checks.

1. Update `VERSION` in `openmd`, add the version's `## <version>` entry to `CHANGELOG.md`, and update user-facing documentation.
2. Run local checks:

   ```bash
   bash -n openmd
   python3 tests/smoke.py
   python3 scripts/package.py v0.5
   ```

   Replace `v0.5` with the version being released. Packaging checks that the tag matches `openmd --version` and runs smoke tests against the executable extracted from the archive.

3. Run the browser checks (Node.js is needed only for tests):

   ```bash
   tools_dir=$(mktemp -d)
   npm install --prefix "$tools_dir" --no-package-lock playwright@1.60.0
   "$tools_dir/node_modules/.bin/playwright" install chromium
   PLAYWRIGHT_MODULE="$tools_dir/node_modules/playwright" node tests/browser.cjs
   rm -rf "$tools_dir"
   ```

4. Commit and push the changes, then create and push an annotated tag:

   ```bash
   git push origin main
   git tag -a v0.5 -m "openmd 0.5"
   git push origin v0.5
   ```

5. Watch **Test and release** in GitHub Actions. The tag run creates a draft release, uploads `openmd`, `openmd-<version>.tar.gz`, and `SHA256SUMS`, downloads and verifies those assets, then publishes the release and verifies the public executable download. Inspect the completed run and the release assets before announcing success.

The raw executable works on macOS and Linux with Bash and Python 3; it is not architecture-specific. The archive includes the README and changelog. Users downloading the raw executable need `chmod +x openmd`.

Published tags/releases must not be moved or overwritten. If a run fails before publication, inspect the error and remove only its incomplete draft release before rerunning the failed jobs. If it fails after publication, inspect and retry verification; use a new version for code fixes.
