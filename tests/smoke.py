import atexit, json, os, pathlib, re, shutil, subprocess, sys, tempfile
cli = str(pathlib.Path(os.environ.get('OPENMD_CLI', pathlib.Path(__file__).resolve().parents[1] / 'openmd')).resolve())
root = pathlib.Path(tempfile.mkdtemp(prefix='openmd-check-'))
if '--keep-fixture' not in sys.argv:
    atexit.register(shutil.rmtree, root)
repo = root / 'repo space # ü'
repo.mkdir()
out = root / 'output'
out.mkdir()

def run(*args, cwd=repo, env=None, ok=True):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    return result.stdout.strip()

def git(*args):
    return run('git', *args)

def generate(path, *args, env=None):
    output = run(cli, *args, str(path), env=env or {**os.environ, 'OPENMD_OUTPUT_DIR': str(out), 'OPENMD_NO_OPEN': '1'})
    assert output.startswith('openmd: wrote '), output
    preview = pathlib.Path(output[len('openmd: wrote '):])
    html = preview.read_text()
    match = re.search(r'git: (.*),\n', html)
    return preview, json.loads(match[1]), html

git('init', '-b', 'main')
git('config', 'user.email', 'test@example.invalid')
git('config', 'user.name', 'Test')
(repo/'docs').mkdir()
(repo/'data').mkdir()
(repo/'docs/images').mkdir()
image = repo/'docs/images/chart # ü.svg'
image.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="red"/></svg>')
(repo/'data/results final.csv').write_text('name,value\na,42\n')
md = repo/'docs/report [1].md'
links = '''
[CSV](../data/results%20final.csv)
[Section](#results)
[Malformed](#bad%ZZ)
[External](https://example.com/test)
![Markdown image](images/chart%20%23%20%C3%BC.svg)
<img alt="HTML image" src="images/chart%20%23%20%C3%BC.svg">
<img alt="Srcset image" srcset="images/chart%20%23%20%C3%BC.svg 1x">
## Results
Literal __FILE_JSON__ and </script> remain text.
'''
md.write_text('# Committed\n'+links)
git('add', '.')
git('commit', '-m', 'initial')
git('checkout', '-b', 'feature/docs')
md.write_text('# Branch version\n'+links)
git('commit', '-am', 'branch')
git('checkout', '-b', 'missing')
git('rm', str(md))
git('commit', '-m', 'remove')
git('checkout', 'main')
md.write_text('# Staged\n'+links)
git('add', str(md))
md.write_text('# Working copy\n'+links)
(repo/'untracked.txt').write_text('untracked')
before = git('status', '--porcelain=v1')
preview, data, html = generate(md)
assert before == git('status', '--porcelain=v1')
assert data['branch'] == 'main'
assert data['repositoryStatus'] == 'staged changes, unstaged changes, untracked files', data
assert data['fileStatus'] == 'staged changes, unstaged changes'
versions = {v['label']:v for v in data['versions']}
assert versions['Working copy']['markdown'].startswith('# Working copy')
assert versions['Last committed version (HEAD)']['markdown'].startswith('# Committed')
assert versions['Branch: feature/docs']['markdown'].startswith('# Branch version')
assert versions['Branch: missing']['markdown'] is None
assert '__FILE_JSON__' in versions['Working copy']['markdown']
assert 'repo%20space%20%23%20%C3%BC/docs/' in html
# Detached HEAD, clean status, linked worktree, untracked, and non-repository input.
git('checkout', '--detach', 'HEAD')
_, detached, _ = generate(md)
assert detached['branch'].startswith('Detached HEAD at ')
git('reset', '--hard', 'HEAD')
(repo/'untracked.txt').unlink()
_, clean, _ = generate(md)
assert clean['repositoryStatus'] == clean['fileStatus'] == 'clean'
worktree = root/'linked worktree'
git('worktree', 'add', str(worktree), 'feature/docs')
_, wt, _ = generate(worktree/'docs/report [1].md')
assert wt['branch'] == 'feature/docs'
(repo/'new.md').write_text('# New')
assert generate(repo/'new.md')[1] is None
outside = root/'outside.md'
outside.write_text('# Outside')
assert generate(outside)[1] is None
# Staged addition before first commit.
unborn = root/'unborn'
unborn.mkdir()
run('git', 'init', '-b', 'new', cwd=unborn)
(unborn/'new.md').write_text('# New')
run('git', 'add', 'new.md', cwd=unborn)
_, fresh, _ = generate(unborn/'new.md')
assert fresh['branch'] == 'new (no commits yet)'
assert len(fresh['versions']) == 1
# No launcher may run for either suppression mechanism.
bin_dir = root/'bin'
bin_dir.mkdir()
marker = root/'launcher-called'
for launcher in ('open', 'xdg-open', 'start'):
    path = bin_dir/launcher
    path.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\n')
    path.chmod(0o755)
env = {**os.environ, 'PATH': str(bin_dir)+os.pathsep+os.environ['PATH'], 'OPENMD_OUTPUT_DIR':str(out)}
env.pop('OPENMD_NO_OPEN', None)
generate(outside, '--no-open', '--title', 'Custom title', env=env)
generate(outside, env={**env, 'OPENMD_NO_OPEN':'1'})
assert not marker.exists()
assert 'Git working-copy' in run(cli, '--help')
for args in ([], ['--bad'], ['--title'], ['missing.md'], [str(md), str(md)]):
    run(cli, *args, ok=False)
run(cli, '--no-open', str(md), env={**env, 'OPENMD_OUTPUT_DIR':str(root/'missing')}, ok=False)
# Git absent from PATH is supported (supply only existing runtime tools).
minimal = root/'minimal-bin'
minimal.mkdir()
for command in ('bash', 'python3', 'basename', 'date', 'mktemp', 'mv'):
    (minimal/command).symlink_to(shutil.which(command))
_, no_git, _ = generate(md, env={**env, 'PATH':str(minimal), 'OPENMD_NO_OPEN':'1'})
assert no_git is None
(root/'manifest.json').write_text(json.dumps({'preview':str(preview), 'root':str(root), 'source':str(md), 'csv':str(repo/'data/results final.csv'), 'image':str(image)}))
print('PASS: CLI, Git versions/status, detached HEAD, unborn branch, linked worktree, no Git, no browser launch, invalid arguments')
print(root/'manifest.json')
