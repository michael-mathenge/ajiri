"""Copy private documents without changing names, database rows or source files."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from jobs.models import Application
from profiles.models import Profile


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def inside(path, root):
    return path == root or root in path.parents


def reject_links(path):
    if any(part.is_symlink() or part.is_junction() for part in (path, *path.parents)):
        raise CommandError('Symlink paths are not permitted.')


class Command(BaseCommand):
    # see docs/CONCEPTS.md#private-media-storage
    help = 'Inventory or copy media to private storage; never delete files or update rows.'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True)
        parser.add_argument('--destination', required=True)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('--dry-run', action='store_true')
        mode.add_argument('--apply', action='store_true')
        mode.add_argument('--verify', action='store_true')
        parser.add_argument('--manifest')

    def handle(self, *args, **options):
        try:
            self.relocate(options)
        except (OSError, ValueError) as error:
            # Avoid disclosing document names or machine paths in shared logs.
            raise CommandError('Filesystem operation failed; inspect permissions, space and paths privately.') from error

    def relocate(self, options):
        source, destination = (Path(options[key]) for key in ('source', 'destination'))
        if not source.is_absolute() or not destination.is_absolute():
            raise CommandError('Both roots must be absolute.')
        reject_links(source)
        reject_links(destination)
        source, destination = source.resolve(), destination.resolve()
        if source == Path(source.anchor) or destination == Path(destination.anchor):
            raise CommandError('Filesystem roots are not permitted.')
        if inside(source, destination) or inside(destination, source):
            raise CommandError('Roots must be distinct and must not contain one another.')
        if not source.is_dir() or (destination.exists() and not destination.is_dir()):
            raise CommandError('Source must exist as a directory and destination must be a directory.')
        public_roots = [settings.STATIC_ROOT, settings.BASE_DIR / 'frontend_build', settings.BASE_DIR / 'media']
        public_roots += [item[1] if isinstance(item, (tuple, list)) else item for item in settings.STATICFILES_DIRS]
        for public in public_roots:
            if public and inside(destination, Path(public).resolve()):
                raise CommandError('Destination must be outside known public asset roots.')

        names = set(Profile.objects.exclude(cv_file='').exclude(cv_file__isnull=True).values_list('cv_file', flat=True))
        for cv, letter in Application.objects.values_list('generated_cv', 'generated_cover_letter'):
            names.update(name for name in (cv, letter) if name)
        for name in names:
            parsed = PurePosixPath(name)
            if parsed.is_absolute() or '..' in parsed.parts or '\\' in name or ':' in name:
                raise CommandError('An unsafe database file reference blocks relocation.')
            path = source / name
            reject_links(path)
            if not inside(path.resolve(), source) or not path.is_file():
                raise CommandError('A referenced file is missing or unsafe; relocation aborted.')

        records = []
        for directory, folders, files in os.walk(source, followlinks=False):
            for name in folders + files:
                reject_links(Path(directory) / name)
            for name in files:
                path = Path(directory) / name
                if not path.is_file():
                    raise CommandError('Unsupported source entry.')
                relative = path.relative_to(source).as_posix()
                target = destination / relative
                reject_links(target)
                if not inside(target.resolve(), destination):
                    raise CommandError('Destination escaped its root.')
                checksum = digest(path)
                if target.exists() and (not target.is_file() or digest(target) != checksum):
                    raise CommandError('Destination content conflict; nothing overwritten.')
                if options['verify'] and not target.is_file():
                    raise CommandError('Verification failed: destination file missing.')
                records.append(dict(name=relative, size=path.stat().st_size, sha256=checksum,
                                    referenced=relative in names,
                                    status='already-identical' if target.exists() else 'planned'))

        manifest = Path(options['manifest']) if options['manifest'] else None
        if manifest:
            if not manifest.is_absolute():
                raise CommandError('Manifest path must be absolute.')
            reject_links(manifest)
            if inside(manifest.resolve(), source) or inside(manifest.resolve(), destination):
                raise CommandError('Keep the manifest outside both media roots.')
            if any(public and inside(manifest.resolve(), Path(public).resolve()) for public in public_roots):
                raise CommandError('Manifest must be outside known public asset roots.')
            if options['apply'] and (manifest.exists() or not manifest.parent.is_dir()):
                raise CommandError('Use a new manifest in an existing private audit directory.')

        if options['apply']:
            ancestor = destination
            while not ancestor.exists():
                ancestor = ancestor.parent
            required = sum(row['size'] for row in records if row['status'] == 'planned')
            if shutil.disk_usage(ancestor).free < required + 1024 * 1024:
                raise CommandError('Insufficient free destination space.')
            destination.mkdir(parents=True, exist_ok=True, mode=0o700)
            for row in records:
                target = destination / row['name']
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                # Existing parent directories may predate the command.
                for parent in (target.parent, *target.parent.parents):
                    if not inside(parent, destination):
                        break
                    parent.chmod(0o700)
                if row['status'] == 'planned':
                    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix='.relocate-')
                    try:
                        with os.fdopen(handle, 'wb') as output, (source / row['name']).open('rb') as original:
                            shutil.copyfileobj(original, output)
                            output.flush()
                            os.fsync(output.fileno())
                        if digest(Path(temporary)) != row['sha256']:
                            raise CommandError('Source changed during copy; keep writers paused.')
                        # Atomic, exclusive publication: unlike replace(), link() cannot overwrite.
                        os.link(temporary, target)
                        row['status'] = 'copied'
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                target.chmod(0o600)
                if digest(target) != row['sha256']:
                    raise CommandError('Destination verification failed.')
            if manifest:
                descriptor = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
                    json.dump(records, output, indent=2)
            self.stdout.write('Copy complete; source files and database unchanged.')
        else:
            self.stdout.write('Verified.' if options['verify'] else 'Dry-run: no filesystem or database writes.')
            if manifest:
                self.stdout.write('Manifest requested; read-only mode did not write it.')
        self.stdout.write(f"Files: {len(records)}; referenced names: {len(names)}; orphans: {sum(not row['referenced'] for row in records)}")
