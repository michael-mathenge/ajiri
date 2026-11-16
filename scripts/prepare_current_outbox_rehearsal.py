"""Prepare a source-only context for the current registered outbox worker lab."""
from pathlib import Path
import shutil
from prepare_storage_rehearsal import prepare


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    target = prepare(root)
    shutil.copy2(root/'scripts/current_outbox_rehearsal.py', target/'rehearsal.py')
    shutil.copy2(root/'scripts/queue-rehearsal/Dockerfile', target/'Dockerfile')
    print(target)
