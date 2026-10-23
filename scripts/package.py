#!/usr/bin/env python3
"""Build and smoke-test the exact standalone release downloads."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
version = subprocess.check_output([str(root / 'openmd'), '--version'], text=True).strip().split()[-1]
if len(sys.argv) != 2 or sys.argv[1] != 'v' + version or not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', version):
    sys.exit('Usage: python3 scripts/package.py v<VERSION> (must match openmd --version)')
out = root / 'dist'
if out.exists():
    shutil.rmtree(out)
out.mkdir()
files = ['openmd', 'README.md', 'CHANGELOG.md']
shutil.copy2(root / 'openmd', out / 'openmd')
if (root / 'install.sh').exists():
    files.append('install.sh')
    shutil.copy2(root / 'install.sh', out / 'install.sh')
archive = out / ('openmd-' + version + '.tar.gz')
with tarfile.open(archive, 'w:gz') as tar:
    for name in files:
        tar.add(root / name, arcname='openmd-' + version + '/' + name)
with tempfile.TemporaryDirectory(prefix='openmd-package-') as temp:
    with tarfile.open(archive) as tar:
        tar.extractall(temp)
    installed = Path(temp) / ('openmd-' + version) / 'openmd'
    subprocess.run(['python3', str(root / 'tests/smoke.py')], env={**os.environ, 'OPENMD_CLI': str(installed)}, check=True)
(out / 'SHA256SUMS').write_text(''.join(
    hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n'
    for path in sorted(out.iterdir())
))
if (out / 'install.sh').exists():
    subprocess.run(['python3', str(root / 'tests/install.py')], check=True)
print('Release downloads:', out)
