from pathlib import Path
import shutil
from prepare_storage_rehearsal import prepare


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    target = prepare(root)
    shutil.copy2(root/'scripts/storage_rehearsal.py', target/'storage_helpers.py')
    shutil.copy2(root/'scripts/postgres_bootstrap_rehearsal.py', target/'rehearsal.py')
    dockerfile = target/'Dockerfile'
    with dockerfile.open('a') as stream:
        stream.write('\nCOPY storage_helpers.py /app/storage_helpers.py\n')
    print(target)
