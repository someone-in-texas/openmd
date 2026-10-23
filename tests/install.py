"""Test the packaged installer through stdin, including failures and upgrades."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
version = subprocess.check_output([str(root / 'openmd'), '--version'], text=True).strip().split()[-1]
with tempfile.TemporaryDirectory(prefix='openmd-install-test-') as temp:
    temp = Path(temp)
    assets = temp / 'assets'
    shutil.copytree(root / 'dist', assets)
    fake_bin = temp / 'bin'
    fake_bin.mkdir()
    curl = fake_bin / 'curl'
    curl.write_text('''#!/usr/bin/env python3
import os, pathlib, shutil, sys
args = sys.argv[1:]
url = next(arg for arg in args if arg.startswith('https://'))
expected = 'https://github.com/someone-in-texas/openmd/releases/download/v' + os.environ['TEST_VERSION'] + '/'
assert url.startswith(expected), url
if os.environ.get('TEST_DOWNLOAD_FAIL'):
    sys.exit(22)
source = pathlib.Path(os.environ['TEST_ASSETS']) / url[len(expected):]
if not source.is_file():
    sys.exit(22)
shutil.copyfile(source, args[args.index('-o') + 1])
''')
    curl.chmod(0o755)
    target = temp / 'install space ü'
    env = {**os.environ, 'PATH': str(fake_bin) + os.pathsep + os.environ['PATH'],
           'OPENMD_INSTALL_DIR': str(target),
           'TEST_VERSION': version, 'TEST_ASSETS': str(assets)}
    env.pop('OPENMD_VERSION', None)
    script = (root / 'dist/install.sh').read_text()
    bash = shutil.which('bash')

    def install(ok=True, **overrides):
        result = subprocess.run([bash], input=script, text=True, capture_output=True,
                                env={**env, **overrides})
        assert (result.returncode == 0) == ok, (result.stdout, result.stderr)
        assert not list(target.glob('.openmd.*')), 'temporary install file leaked'
        return result

    install()
    executable = target / 'openmd'
    expected = (assets / 'openmd').read_bytes()
    assert executable.read_bytes() == expected
    assert os.access(executable, os.X_OK)
    assert subprocess.check_output([str(executable), '--version'], text=True).strip() == 'openmd ' + version
    markdown = temp / 'sample.md'
    markdown.write_text('# Installed preview')
    subprocess.run([str(executable), '--no-open', str(markdown)],
                   env={**os.environ, 'OPENMD_OUTPUT_DIR': str(temp)}, check=True, capture_output=True)
    executable.write_text('old installation')
    install(OPENMD_VERSION='v' + version)
    assert executable.read_bytes() == expected, 'upgrade failed'
    for overrides in ({'TEST_DOWNLOAD_FAIL':'1'}, {'OPENMD_VERSION':'../../bad'}):
        install(False, **overrides)
        assert executable.read_bytes() == expected
    (assets / 'openmd').write_bytes(b'corrupted download')
    assert 'checksum verification failed' in install(False).stderr
    assert executable.read_bytes() == expected
    # Even a matching checksum must not permit an unexpected executable version.
    wrong = b'#!/usr/bin/env bash\necho "openmd 999.0"\n'
    (assets / 'openmd').write_bytes(wrong)
    (assets / 'SHA256SUMS').write_text(hashlib.sha256(wrong).hexdigest() + '  openmd\n')
    assert 'wrong version' in install(False).stderr
    assert executable.read_bytes() == expected
    (assets / 'SHA256SUMS').unlink()
    install(False)
    assert executable.read_bytes() == expected
    assert 'required command python3 not found' in install(False, PATH=str(fake_bin)).stderr
    # A directory at the destination must not silently receive the executable.
    shutil.copy2(root / 'dist/openmd', assets / 'openmd')
    shutil.copy2(root / 'dist/SHA256SUMS', assets / 'SHA256SUMS')
    executable.unlink()
    executable.mkdir()
    assert 'destination is a directory' in install(False).stderr
    assert not list(executable.iterdir())
print('PASS: piped installer, executable preview, upgrades, version pins, failed downloads, corrupt checksums, wrong versions, missing dependencies, directory destination')
