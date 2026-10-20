"""Private snapshots; retention is advisory and never removes data."""
from datetime import datetime, timedelta, timezone
from contextlib import closing
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import stat
import subprocess
import tarfile
import time
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from config.paths import application_tree


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def no_links(path):
    for item in [path, *path.parents]:
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise CommandError('Backup paths must not contain links or junctions.')


def source_revision():
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=settings.BASE_DIR,
                                capture_output=True, text=True, check=True)
        revision = result.stdout.strip()
        if re.fullmatch(r'[0-9a-f]{40}', revision):
            return revision
    except (OSError, subprocess.CalledProcessError):
        pass
    # Missing build provenance must be explicit, not prevent protecting local data.
    return 'unverified'


def media_inventory(root):
    no_links(root)
    if not root.is_dir():
        raise CommandError('Private media directory is missing.')
    inventory = {}
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(current) / name
            info = path.lstat()
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or path.is_symlink():
                raise CommandError('Media contains an unsupported entry; no snapshot created.')
            if name == '.env' or name.startswith('.env.') or name == 'environment.backup':
                raise CommandError('Media contains a credential-file name; archive refused.')
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    raise CommandError('Media hard links are not supported.')
                inventory[path.relative_to(root)] = (info.st_size, info.st_mtime_ns, info.st_ino)
    return inventory


def backup_sqlite(source, destination):
    deadline = time.monotonic() + 60
    def progress(status, remaining, total):
        if time.monotonic() > deadline:
            raise TimeoutError('Backup time budget exceeded.')
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=20)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst, pages=100, progress=progress, sleep=0.01)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup integrity check failed.')


def retention_candidates(destination, days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    candidates = []
    if not destination.exists():
        return candidates
    for folder in destination.glob('backup-*'):
        if not folder.is_dir() or folder.is_symlink():
            continue
        manifest = folder / 'manifest.json'
        if manifest.is_symlink():
            continue
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if data.get('format') == 1 and data.get('complete') is True and datetime.fromisoformat(data['created_at']) < cutoff:
                candidates.append(folder.name)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(candidates)


class Command(BaseCommand):
    help = 'Back up private SQLite data; optional paused-writer media; retention is report-only.'
    # see docs/CONCEPTS.md#private-backup-snapshots
    def add_arguments(self, parser):
        parser.add_argument('--destination', required=True)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--include-media', action='store_true')
        parser.add_argument('--writers-paused', action='store_true')
        parser.add_argument('--retention-days', type=int, default=int(os.environ.get('BACKUP_RETENTION_DAYS', '30')))

    def handle(self, *args, **options):
        destination = Path(options['destination'])
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command supports SQLite only.')
        source = Path(database['NAME'])
        media = Path(settings.MEDIA_ROOT)
        if not destination.is_absolute() or options['retention_days'] < 1:
            raise CommandError('Use an absolute private destination and positive retention days.')
        for path in [source, media, destination]:
            no_links(path)
        source, media, destination = source.resolve(), media.resolve(), destination.resolve()
        if not source.is_file():
            raise CommandError('Configured SQLite database must exist as a regular file.')
        if (destination.is_relative_to(application_tree(settings.BASE_DIR))
                or destination.is_relative_to(source.parent)
                or destination.is_relative_to(media) or media.is_relative_to(destination)):
            raise CommandError('Destination must be outside application, database and media trees.')
        if destination.exists() and not destination.is_dir():
            raise CommandError('Destination must be a private directory.')
        if destination.exists() and os.name != 'nt':
            info = destination.stat()
            if info.st_mode & 0o077 or info.st_uid != os.getuid():
                raise CommandError('Destination must be owned by this account with 0700 permissions.')
        if options['include_media'] and not options['dry_run'] and not options['writers_paused']:
            raise CommandError('Media snapshots require --writers-paused after pausing all writers.')
        inventory = media_inventory(media) if options['include_media'] else {}
        candidates = retention_candidates(destination, options['retention_days'])
        self.stdout.write(f'Retention DRAFT: {options["retention_days"]} days; {len(candidates)} candidates; no deletion.')
        for name in candidates:
            self.stdout.write('Candidate: ' + name)
        if options['dry_run']:
            self.stdout.write(f'DRY RUN: SQLite backup; media files={len(inventory)}; no writes.')
            return
        destination.mkdir(mode=0o700, parents=True, exist_ok=True)
        name = 'backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
        partial = destination / ('.partial-' + name)
        partial.mkdir(mode=0o700)
        try:
            target_db = partial / 'db.sqlite3'
            backup_sqlite(source, target_db)
            target_db.chmod(0o600)
            hashes = {'db.sqlite3': digest(target_db)}
            if options['include_media']:
                archive = partial / 'private-media.tar.gz'
                with tarfile.open(archive, 'w:gz', dereference=False) as tar:
                    for relative in sorted(inventory):
                        tar.add(media / relative, arcname=str(relative), recursive=False)
                archive.chmod(0o600)
                with gzip.open(archive, 'rb') as stream:
                    while stream.read(1024 * 1024):
                        pass
                if inventory != media_inventory(media):
                    raise ValueError('Media changed during the paused-writer window.')
                hashes[archive.name] = digest(archive)
                with gzip.open(archive, 'rb') as stream:
                    hashes['media_uncompressed'] = hashlib.file_digest(stream, 'sha256').hexdigest()
            revision = source_revision()
            manifest = {'format': 1, 'complete': True, 'created_at': datetime.now(timezone.utc).isoformat(),
                        'revision': revision, 'sha256': hashes, 'media_included': options['include_media'],
                        'media_files': len(inventory), 'media_bytes': sum(v[0] for v in inventory.values()),
                        'retention_days_draft': options['retention_days']}
            marker = partial / 'manifest.json'
            marker.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            marker.chmod(0o600)
            partial.rename(destination / name)
        except Exception as error:
            raise CommandError('Backup incomplete; private partial folder retained; no completed snapshot published.') from error
        self.stdout.write('Backup verified: ' + name)
