"""Operator for disposable labelled Docker resources, with no host mounts or ports.

see docs/CONCEPTS.md#combined-recovery-rehearsal
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid


IMAGE = 'ajiri-combined-recovery:20261120'
LABEL = 'ajiri.synthetic-combined-recovery'


def docker(*args, data=None, timeout=120, expected=0):
    result = subprocess.run(['docker', *args], input=data, capture_output=True, timeout=timeout)
    if result.returncode != expected:
        raise RuntimeError(f'Docker {args[0]} failed ({result.returncode}): '+result.stderr.decode(errors='replace')[-3000:]
            +result.stdout.decode(errors='replace')[-4000:])
    return result.stdout


def wait(predicate, timeout=45):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.5)
    raise RuntimeError('Synthetic service readiness timed out.')


class Lab:
    def __init__(self, output):
        self.identity = uuid.uuid4().hex
        self.output = output
        self.resources = []

    def create(self, name, image, args, *, network='none', tmpfs=(), extra=()):
        command = ['run', '-d', '--name', f'ajiri-combined-{self.identity[:10]}-{name}',
            '--label', LABEL+'='+self.identity, '--network', network,
            '--cpus', '1', '--memory', '512m', '--pids-limit', '128', '--read-only',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m', *extra]
        for item in tmpfs:
            command.extend(['--tmpfs', item])
        identity = docker(*command, image, *args).decode().strip()
        self.resources.append(identity)
        info = json.loads(docker('inspect', identity))[0]
        if info['HostConfig']['Binds'] or info['HostConfig']['PortBindings']:
            raise RuntimeError('Synthetic lab must have no host mounts or published ports.')
        if any(m['Type'] != 'tmpfs' for m in info['Mounts']):
            raise RuntimeError('Only disposable tmpfs storage is permitted.')
        return identity

    def stack(self, name, *, restore=False):
        pg = self.create(name+'-db', 'postgres:17.12-bookworm', [],
            tmpfs=('/var/lib/postgresql/data:rw,nosuid,nodev,size=128m',
                   '/var/run/postgresql:rw,nosuid,nodev,size=1m'),
            extra=('-e', 'POSTGRES_HOST_AUTH_METHOD=trust'))
        wait(lambda: subprocess.run(['docker', 'exec', pg, 'pg_isready', '-U', 'postgres'],
            capture_output=True).returncode == 0)
        command = ['sh', '-c', 'while [ ! -f /data/restore-ready ]; do sleep 0.2; done; exec redis-server --bind 127.0.0.1 --appendonly no'] if restore else [
            'redis-server', '--bind', '127.0.0.1', '--appendonly', 'yes', '--appendfsync', 'always']
        redis = self.create(name+'-broker', 'redis:8-alpine', command,
            network='container:'+pg, tmpfs=('/data:rw,nosuid,nodev,size=32m',))
        moto = self.create(name+'-objects', IMAGE, ['moto_server', '-H', '127.0.0.1', '-p', '5000'],
            network='container:'+pg)
        app = self.create(name+'-app', IMAGE, ['python', '-c', 'import time;time.sleep(3600)'],
            network='container:'+pg)
        wait(lambda: subprocess.run(['docker', 'exec', app, 'python', '-c',
            "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000',timeout=2).close()"],
            capture_output=True).returncode == 0)
        if not restore:
            wait(lambda: subprocess.run(['docker', 'exec', redis, 'redis-cli', 'ping'],
                capture_output=True).stdout.strip() == b'PONG')
        return {'pg': pg, 'redis': redis, 'moto': moto, 'app': app}

    def stop(self, identities):
        for identity in reversed(identities):
            info = json.loads(docker('inspect', identity))[0]
            if info['Config']['Labels'].get(LABEL) != self.identity:
                raise RuntimeError('Refusing to stop a resource outside this invocation.')
            if info['State']['Running']:
                docker('stop', '--time', '10', identity, timeout=30)
        assert all(not json.loads(docker('inspect', i))[0]['State']['Running'] for i in identities)

    def phase(self, app, phase, expected=0):
        try:
            output = docker('exec', app, 'python', '/combined_recovery_rehearsal.py', phase,
                expected=expected, timeout=240)
        except Exception as error:
            (self.output/(phase+'-failure.txt')).write_text(str(error), encoding='utf-8')
            diagnostics = docker('exec', app, 'python', '-c',
                "from pathlib import Path;[print(p.name,p.read_text()[-6000:]) for p in Path('/tmp/combined-state').glob('worker-*.log')]")
            (self.output/(phase+'-worker-failure.log')).write_bytes(diagnostics)
            print(str(error)[-4500:], flush=True)
            raise
        (self.output/(phase+'.log')).write_bytes(output)
        print(output.decode(errors='replace')[-1800:], flush=True)

    def read(self, container, path, *, limit):
        code = 'import base64,pathlib;print(base64.b64encode(pathlib.Path('+repr(path)+').read_bytes()).decode())'
        encoded = docker('exec', container, 'python', '-c', code)
        if len(encoded) > (limit+2)//3*4+2:
            raise RuntimeError('Synthetic artifact exceeds reviewed bound.')
        data = base64.b64decode(encoded, validate=False)
        if len(data) > limit:
            raise RuntimeError('Synthetic artifact exceeds reviewed bound.')
        return data

    def write(self, container, path, data, *, python='python'):
        if len(data) > 64*1024*1024:
            raise RuntimeError('Synthetic import exceeds reviewed bound.')
        code = ('import base64,pathlib,sys;p=pathlib.Path('+repr(path)+');'
            "p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(base64.b64decode(sys.stdin.buffer.read(),validate=True))")
        docker('exec', '-i', container, python, '-c', code, data=base64.b64encode(data))

    def run(self):
        started = time.monotonic()
        source = self.stack('source')
        self.phase(source['app'], 'source')
        source_stats = docker('stats', '--no-stream', '--format', '{{json .}}', *source.values()).decode()
        (self.output/'source-resource-sample.jsonl').write_text(source_stats)
        # Writers are stopped before consistent PG/RDB/object snapshots are exported.
        docker('exec', source['redis'], 'redis-cli', 'SAVE')
        docker('exec', source['pg'], 'pg_dump', '-U', 'postgres', '-Fc', '-f', '/tmp/combined.dump', 'postgres')
        dump = docker('exec', source['pg'], 'cat', '/tmp/combined.dump')
        rdb = docker('exec', source['redis'], 'cat', '/data/dump.rdb')
        if len(dump) > 64*1024*1024 or len(rdb) > 8*1024*1024:
            raise RuntimeError('Synthetic dump bound exceeded.')
        pack = '''from pathlib import Path
import zipfile
root=Path('/tmp/combined-state')
with zipfile.ZipFile('/tmp/state.zip','x',zipfile.ZIP_DEFLATED) as archive:
 for p in sorted(root.rglob('*')):
  if p.is_file() and not p.is_symlink() and 'ledger' not in p.relative_to(root).parts:
   archive.write(p,str(p.relative_to(root)))
'''
        docker('exec', source['app'], 'python', '-c', pack)
        state = self.read(source['app'], '/tmp/state.zip', limit=10*1024*1024)
        for name, data in [('database.dump', dump), ('broker.rdb', rdb), ('state.zip', state)]:
            (self.output/name).write_bytes(data)
        (self.output/'source-checkpoint.json').write_text(json.dumps({'resources': source,
            'invocation_label': self.identity, 'writers_stopped': True}, indent=2))
        self.stop(source.values())
        target = self.stack('target', restore=True)
        assert not set(source.values()) & set(target.values())
        docker('exec', '-i', target['pg'], 'sh', '-c', 'cat > /tmp/combined.dump', data=dump)
        docker('exec', target['pg'], 'pg_restore', '-U', 'postgres', '--single-transaction',
            '--exit-on-error', '--no-owner', '--no-privileges', '-d', 'postgres', '/tmp/combined.dump')
        # Redis has no Python; stdin bytes avoid shell interpolation and host mounts.
        docker('exec', '-i', target['redis'], 'sh', '-c', 'cat > /data/dump.rdb', data=rdb)
        assert docker('exec', target['redis'], 'cat', '/data/dump.rdb') == rdb
        docker('exec', target['redis'], 'touch', '/data/restore-ready')
        wait(lambda: subprocess.run(['docker', 'exec', target['redis'], 'redis-cli', 'ping'],
            capture_output=True).stdout.strip() == b'PONG')
        docker('exec', target['redis'], 'redis-cli', 'CONFIG', 'SET', 'appendonly', 'yes')
        self.write(target['app'], '/tmp/state.zip', state)
        extract = '''from pathlib import Path,PurePosixPath
import zipfile
root=Path('/tmp/combined-state');root.mkdir()
with zipfile.ZipFile('/tmp/state.zip') as archive:
 infos=archive.infolist();names=[i.filename for i in infos]
 assert len(names)==len(set(names)) and len(names)<200 and sum(i.file_size for i in infos)<20*1024*1024
 for info in infos:
  name=PurePosixPath(info.filename)
  assert not name.is_absolute() and '..' not in name.parts and '\\\\' not in info.filename and not info.is_dir()
  p=root.joinpath(*name.parts);p.parent.mkdir(parents=True,exist_ok=True)
  p.open('xb').write(archive.read(info))
'''
        docker('exec', target['app'], 'python', '-c', extract)
        self.phase(target['app'], 'database', expected=72)
        self.phase(target['app'], 'copy', expected=73)
        self.phase(target['app'], 'ready', expected=74)
        self.stop(source.values())  # Independent second authority check before worker activation.
        self.write(target['app'], '/tmp/combined-state/source-stopped', b'verified-by-host')
        self.phase(target['app'], 'worker')
        target_stats = docker('stats', '--no-stream', '--format', '{{json .}}', *target.values()).decode()
        (self.output/'target-resource-sample.jsonl').write_text(target_stats)
        receipt = {'synthetic_only': True, 'source_resources': source, 'fresh_target_resources': target,
            'source_stopped_before_target': True, 'interrupted_boundaries': 3,
            'elapsed_seconds': round(time.monotonic()-started, 3),
            'resource_samples_are_not_peaks': True,
            'images': {name: json.loads(docker('image', 'inspect', name))[0]['Id']
                for name in (IMAGE, 'postgres:17.12-bookworm', 'redis:8-alpine')},
            'artifact_sha256': {name: hashlib.sha256((self.output/name).read_bytes()).hexdigest()
                for name in ('database.dump', 'broker.rdb', 'state.zip')},
            'physical_host_loss_verified': False, 'production_activation': False}
        (self.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print('Combined fresh-stack recovery passed. Artifacts: '+str(self.output), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] != ['--synthetic-only']:
        raise SystemExit('Pass --synthetic-only explicitly; Docker resources must be disposable.')
    root = Path(__file__).resolve().parents[1]/'.verification'
    root.mkdir(exist_ok=True)
    output = root/('combined-recovery-'+uuid.uuid4().hex)
    output.mkdir()
    lab = Lab(output)
    try:
        lab.run()
    finally:
        # Retain labelled stopped resources and artifacts for review/recovery; no Docker pruning.
        lab.stop(lab.resources)
