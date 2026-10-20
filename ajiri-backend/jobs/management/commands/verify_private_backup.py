"""Independent verification/isolated restoration; never modifies live data."""
from contextlib import closing
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
from django.core.management.base import BaseCommand, CommandError
from config.paths import application_tree
from django.conf import settings
from .backup_private_data import digest, no_links


class Command(BaseCommand):
    help = 'Verify a completed private backup; optionally restore into a new private folder.'
    # see docs/CONCEPTS.md#verified-backup-restoration

    def add_arguments(self, parser):
        parser.add_argument('--backup', required=True)
        parser.add_argument('--restore-to')
        parser.add_argument('--max-media-bytes', type=int, default=1024 * 1024 * 1024)

    def handle(self, *args, **options):
        try:
            self.verify(options)
        except CommandError:
            raise
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, tarfile.TarError):
            raise CommandError('Backup verification failed; no live data was restored.') from None

    def verify(self, options):
        root = Path(options['backup'])
        if not root.is_absolute() or options['max_media_bytes'] <= 0:
            raise CommandError('Use an absolute backup path and positive media byte limit.')
        no_links(root)
        manifest = root / 'manifest.json'
        no_links(manifest)
        if manifest.stat().st_size > 65536:
            raise CommandError('Backup manifest is too large.')
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if data.get('format') != 1 or data.get('complete') is not True:
            raise CommandError('A completed format-1 backup is required.')
        media = data.get('media_included') is True
        names = {'db.sqlite3'} | ({'private-media.tar.gz', 'media_uncompressed'} if media else set())
        if set(data['sha256']) != names:
            raise CommandError('Backup manifest members are invalid.')
        for name in names - {'media_uncompressed'}:
            no_links(root / name)
            if digest(root / name) != data['sha256'][name]:
                raise CommandError('Backup checksum mismatch.')
        with closing(sqlite3.connect((root/'db.sqlite3').as_uri()+'?mode=ro', uri=True)) as db:
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise CommandError('Backup database integrity failed.')
        count, total = 0, 0
        if media:
            with gzip.open(root/'private-media.tar.gz', 'rb') as stream:
                hashed, expanded = hashlib.sha256(), 0
                while chunk := stream.read(1024 * 1024):
                    expanded += len(chunk)
                    if expanded > options['max_media_bytes'] + 20 * 1024 * 1024:
                        raise CommandError('Expanded backup exceeds verification limits.')
                    hashed.update(chunk)
                if hashed.hexdigest() != data['sha256']['media_uncompressed']:
                    raise CommandError('Uncompressed archive checksum mismatch.')
            seen = set()
            with tarfile.open(root/'private-media.tar.gz', 'r:gz') as archive:
                for item in archive:
                    path = Path(item.name)
                    key = os.path.normcase(str(path))
                    if (len(seen) >= 10000 or key in seen or '\\' in item.name
                            or ':' in item.name
                            or path.is_absolute() or '..' in path.parts
                            or not (item.isfile() or item.isdir())):
                        raise CommandError('Unsafe archive entry.')
                    seen.add(key)
                    if item.isfile():
                        count += 1
                        total += item.size
                    if total > options['max_media_bytes']:
                        raise CommandError('Media exceeds verification limits.')
            if count != data['media_files'] or total != data['media_bytes']:
                raise CommandError('Media inventory mismatch.')
        destination = options.get('restore_to')
        if destination:
            target = Path(destination)
            no_links(target)
            if (not target.is_absolute() or target.exists()
                    or target.resolve().is_relative_to(application_tree(settings.BASE_DIR))
                    or target.resolve() == Path(settings.DATABASES['default']['NAME']).resolve().parent
                    or target.resolve().is_relative_to(Path(settings.MEDIA_ROOT).resolve())):
                raise CommandError('Restore requires a new isolated private destination outside live data.')
            target.mkdir(mode=0o700)
            shutil.copy2(root/'db.sqlite3', target/'db.sqlite3')
            if digest(target/'db.sqlite3') != data['sha256']['db.sqlite3']:
                raise CommandError('Restored database checksum mismatch.')
            with closing(sqlite3.connect((target/'db.sqlite3').as_uri()+'?mode=ro', uri=True)) as db:
                if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise CommandError('Restored database integrity failed.')
            if media:
                restored = target/'media'
                restored.mkdir(mode=0o700)
                with tarfile.open(root/'private-media.tar.gz', 'r:gz') as archive:
                    archive.extractall(restored, filter='data')
                files = [path for path in restored.rglob('*') if path.is_file()]
                if len(files) != count or sum(path.stat().st_size for path in files) != total:
                    raise CommandError('Restored media inventory mismatch.')
                if digest(root/'private-media.tar.gz') != data['sha256']['private-media.tar.gz']:
                    raise CommandError('Archive changed during restoration.')
            (target/'restore-verification.json').write_text(json.dumps({
                'complete': True, 'source_revision': data['revision'],
                'media_files': count, 'media_bytes': total, 'sha256': data['sha256'],
            }, indent=2)+'\n', encoding='utf-8')
        self.stdout.write(f'Backup hashes/database/media verified: {count} files; {total} bytes; '
                          + ('isolated restore complete.' if destination else 'no restore requested; no writes.'))
