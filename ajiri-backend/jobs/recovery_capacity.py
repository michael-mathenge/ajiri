"""Conservative private snapshot/bundle planning; no backup or deletion."""
# see docs/CONCEPTS.md#private-recovery-capacity

MIB = 1024 * 1024


def compressed_bound(size):
    """Allow deflate expansion rather than assuming personal files compress well."""
    return size + size // 4096 + size // 16384 + size // 33554432 + 64


def zip_bound(size, members, name_bytes=0):
    # Per-member allowance includes deflate framing, ZIP records and extra fields.
    return compressed_bound(size) + members * 1024 + name_bytes * 2 + 22


def capacity_plan(*, quota_bytes, used_bytes, database_bytes, media_sizes,
                  ledger_sizes=(), ledger_present=False, reserve_bytes=16 * MIB,
                  extra_snapshot_bytes=0):
    sizes = list(media_sizes)
    ledger = list(ledger_sizes)
    numbers = [quota_bytes, used_bytes, database_bytes, reserve_bytes,
               extra_snapshot_bytes, *sizes, *ledger]
    if any(type(value) is not int or value < 0 for value in numbers) or quota_bytes == 0:
        raise ValueError('Use nonnegative integer byte measurements and a positive quota.')
    # Include tar padding and generous PAX/path metadata per regular private file.
    media_tar = 10240 + sum(((size + 511) // 512) * 512 + 16384 for size in sizes)
    media_archive = compressed_bound(media_tar)
    ledger_archive = zip_bound(sum(ledger), len(ledger), len(ledger) * 4096) if ledger_present else 0
    # A 64 KiB manifest allowance is fixed because snapshots store aggregate counts/hashes.
    snapshot = database_bytes + media_archive + ledger_archive + 65536 + extra_snapshot_bytes
    # Keep the new snapshot AND its transfer ZIP resident; off-server restore is separate.
    bundle = zip_bound(snapshot, 5, 5 * 4096)
    required = snapshot + bundle + reserve_bytes
    available = quota_bytes - used_bytes
    return {
        'dry_run': True,
        'scope': 'sqlite_private_media_erasure_ledger',
        'runtime_recovery_included': False,
        'quota_bytes': quota_bytes,
        'measured_used_bytes': used_bytes,
        'available_bytes': available,
        'database_bytes': database_bytes,
        'media_files': len(sizes),
        'media_bytes': sum(sizes),
        'ledger_files_measured': len(ledger),
        'snapshot_upper_bound_bytes': snapshot,
        'transfer_bundle_upper_bound_bytes': bundle,
        'extra_snapshot_allowance_bytes': extra_snapshot_bytes,
        'reserve_bytes': reserve_bytes,
        'required_additional_bytes': required,
        'remaining_after_plan_bytes': available - required,
        'sufficient': available >= required,
        'retention': 'report_only_no_deletion',
    }
