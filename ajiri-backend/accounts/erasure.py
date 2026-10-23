"""Verified-request erasure with an independently retained recovery journal."""
import os
from pathlib import Path
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import signing
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from config.paths import application_tree
from jobs.management.commands.backup_private_data import no_links
from jobs.models import (Application, ApplicationPackage, ApplicationPackageApproval,
    ApplicationSendAuthorization, ApplicationSendAttemptLink, DeliveryAttempt, DeliveryDailyBudget)
from profiles.models import Profile, CVApproval

SALT = 'ajiri.erasure-journal.v1'


def identity(user):
    return salted_hmac(SALT, str(user.pk) + ':' + user.email.casefold(), algorithm='sha256').hexdigest()


def journal_root(value):
    root = Path(value)
    no_links(root)
    if not root.is_absolute():
        raise CommandError('Use an absolute private journal directory.')
    root = root.resolve()
    forbidden = (application_tree(settings.BASE_DIR), Path(settings.MEDIA_ROOT).resolve(),
                 Path(settings.DATABASES['default']['NAME']).resolve().parent)
    if any(root == p or root.is_relative_to(p) for p in forbidden):
        raise CommandError('Journal must be outside the application and live data directories.')
    if not root.parent.is_dir() or (root.exists() and not root.is_dir()):
        raise CommandError('Journal parent must exist and be a private directory.')
    if os.name != 'nt' and root.exists() and root.stat().st_mode & 0o077:
        raise CommandError('Existing journal directory must have mode0700.')
    return root


def write_journal(path, data):
    # see docs/CONCEPTS.md#recoverable-account-erasure
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    with temporary.open('x', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        stream.write(signing.dumps(data, salt=SALT))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if os.name != 'nt':
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def read_journal(path):
    no_links(path)
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError
        data = signing.loads(path.read_text(encoding='utf-8'), salt=SALT)
        if data['format'] != 1 or data['state'] not in ('prepared', 'db_erased', 'complete'):
            raise ValueError
        return data
    except (signing.BadSignature, KeyError, ValueError, TypeError):
        raise CommandError('Invalid erasure journal; do not proceed with restoration or erasure.') from None


def document_path(name):
    path = Path(settings.MEDIA_ROOT) / name
    no_links(path)
    root = Path(settings.MEDIA_ROOT).resolve()
    if (not name or Path(name).is_absolute() or '..' in Path(name).parts
            or '\\' in name or ':' in name or not path.resolve().is_relative_to(root)):
        raise CommandError('Unsafe private document reference; investigate before erasure.')
    if path.exists() and (not path.is_file() or path.stat().st_nlink > 1):
        raise CommandError('Unsupported private document entry; investigate before erasure.')
    return path


def inventory(user):
    # Employer ownership and moderation can affect other applicants' records.
    # Fail before any writes until a scoped, legally reviewed removal is prepared.
    from jobs.models import EmployerOrganisation, EmployerReview
    if (EmployerOrganisation.objects.filter(Q(owner=user) | Q(reviewed_by=user)).exists()
            or EmployerReview.objects.filter(actor=user).exists()):
        raise CommandError('Employer or moderation records require a reviewed erasure plan before account removal.')
    if (ApplicationPackage.objects.filter(cv_approval__profile__user=user).exclude(application__user=user).exists()
            or ApplicationPackage.objects.filter(application__user=user).exclude(cv_approval__profile__user=user).exists()
            or ApplicationSendAuthorization.objects.filter(application__user=user).exclude(owner=user).exists()
            or ApplicationSendAuthorization.objects.filter(owner=user).exclude(application__user=user).exists()
            or ApplicationPackageApproval.objects.filter(approved_by=user).exclude(package__application__user=user).exists()
            or ApplicationSendAttemptLink.objects.filter(Q(attempt__user=user) | Q(previous_attempt__user=user)).exclude(authorization__owner=user).exists()
            or ApplicationSendAuthorization.objects.filter(owner=user).exclude(document_approval__package__application__user=user).exists()):
        raise CommandError('Cross-owner evidence requires investigation before erasure.')
    if DeliveryAttempt.objects.filter(Q(user=user) | Q(application__user=user) | Q(notification__user=user),
                                      state__in=['reserved', 'unknown']).exists():
        raise CommandError('Unresolved delivery must be reconciled before erasure.')
    scopes = [
        (Profile, 'user', ('cv_file',)),
        (CVApproval, 'profile__user', ('document',)),
        (Application, 'user', ('generated_cv', 'generated_cover_letter')),
        (ApplicationPackage, 'application__user', ('cv_document', 'letter_document')),
    ]
    names = set()
    for model, owner, fields in scopes:
        for row in model.objects.filter(**{owner: user}):
            for field in fields:
                stored = getattr(row, field)
                if stored:
                    document_path(stored.name)
                    names.add(stored.name)
    if len(names) > 10000:
        raise CommandError('Erasure inventory exceeds operator review limits.')
    for name in names:
        for model, owner, fields in scopes:
            for field in fields:
                if model.objects.filter(**{field: name}).exclude(**{owner: user}).exists():
                    raise CommandError('A private file is referenced by another owner; investigate first.')
    return sorted(names)


def erase_rows(user):
    # First database operation claims the writer slot, before eligibility/inventory reads.
    get_user_model().objects.filter(pk=user.pk).update(is_active=False)
    names = inventory(user)
    ApplicationSendAttemptLink.objects.filter(authorization__owner=user).delete()
    ApplicationSendAuthorization.objects.filter(owner=user).delete()
    ApplicationPackageApproval.objects.filter(package__application__user=user).delete()
    ApplicationPackage.objects.filter(application__user=user).delete()
    CVApproval.objects.filter(profile__user=user).delete()
    for session in Session.objects.iterator():
        if str(session.get_decoded().get('_auth_user_id', '')) == str(user.pk):
            session.delete()
    # Keep global quota/settled pseudonymous accounting; remove external receipt identifiers.
    DeliveryAttempt.objects.filter(user=user).update(provider_message_id='')
    DeliveryDailyBudget.objects.filter(scope=f'user:{user.pk}').delete()
    # SimpleJWT retains outstanding token rows with SET_NULL unless explicitly removed.
    OutstandingToken.objects.filter(user=user).delete()
    user.delete()  # Cascades account/profile/app/notifications; receipt links SET_NULL.
    return names


def operate(options):
    mode = options['mode']
    root = journal_root(options['journal_dir'])
    if root != Path(settings.ERASURE_LEDGER_DIR).resolve():
        raise CommandError('Use the configured erasure ledger directory so backups include every journal.')
    request_id = str(uuid.UUID(str(options['request_id'])))
    path = root / (request_id + '.signed')
    user = get_user_model().objects.filter(pk=options['user_id']).first()
    if mode == 'dry-run':
        if user is None:
            raise CommandError('Account not found.')
        return f'DRY RUN: {len(inventory(user))} owned document paths; no writes.'
    required = ('verified_request', 'writers_paused')
    if mode in ('execute', 'replay'):
        required += ('legal_hold_cleared', 'journal_copied')
    if not all(options.get(name) for name in required):
        raise CommandError('Verified request, paused writers and execution recovery/legal attestations are required.')
    if mode == 'prepare':
        if user is None or path.exists():
            raise CommandError('Use an existing owner and a new request identifier.')
        data = {'format': 1, 'request_id': request_id, 'user_id': user.pk, 'identity': identity(user),
                'state': 'prepared', 'files': inventory(user), 'created_at': timezone.now().isoformat()}
        if not root.exists():
            root.mkdir(mode=0o700)
        write_journal(path, data)
        return 'Prepared signed private journal. Preserve a verified off-server copy before execution.'
    data = read_journal(path)
    if data['request_id'] != request_id or data['user_id'] != options['user_id']:
        raise CommandError('Journal does not match this verified request.')
    if user is not None and data['identity'] != identity(user):
        raise CommandError('Account identity differs from journal; never erase a replacement account.')
    if mode == 'replay':
        if data['state'] != 'complete':
            raise CommandError('Replay requires the latest completed erasure ledger.')
        if user is None:
            return 'Completed erasure remains absent; no database changes.'
        data['files'] = inventory(user)
        data['state'] = 'prepared'
        write_journal(path, data)
    elif data['state'] == 'complete':
        if user is not None:
            raise CommandError('Restored account detected; use reviewed replay before reopening writers.')
        return 'Erasure already complete; no changes.'
    if user is not None:
        with transaction.atomic():
            get_user_model().objects.filter(pk=user.pk).update(is_active=False)
            user.refresh_from_db()
            if data['identity'] != identity(user):
                raise CommandError('Account identity changed before erasure; investigate.')
            if sorted(data['files']) != inventory(user):
                raise CommandError('Owner documents changed since preparation; prepare/review a new request.')
            erase_rows(user)
    data['state'] = 'db_erased'
    write_journal(path, data)
    remaining = []
    for name in data['files']:
        try:
            document_path(name).unlink(missing_ok=True)
        except OSError:
            remaining.append(name)
    if remaining:
        data['files'] = remaining
        write_journal(path, data)
        raise CommandError('Account rows erased; file cleanup is pending. Resume the same signed request.')
    data['state'], data['files'] = 'complete', []
    data.setdefault('deleted_at', timezone.now().isoformat())
    write_journal(path, data)
    return 'Erasure complete. Preserve/re-copy the completed journal before any future restore.'
