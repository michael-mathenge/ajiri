"""Export tracked backend source plus explicit synthetic S3 lab files."""
from pathlib import Path
import shutil
from prepare_storage_rehearsal import prepare


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    target = prepare(root)
    shutil.copy2(root/'scripts/private_s3_rehearsal.py', target/'rehearsal.py')
    for name in ('Dockerfile', 'requirements-lab.txt', 's3_lab_backend.py'):
        shutil.copy2(root/'scripts/private-s3-rehearsal'/name, target/name)
    print(target)
