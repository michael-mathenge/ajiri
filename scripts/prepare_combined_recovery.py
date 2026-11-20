"""Export private-free tracked backend and explicit synthetic combined-recovery tools."""
from pathlib import Path
import shutil
from prepare_storage_rehearsal import prepare


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    target = prepare(root)
    for name in ('combined_recovery_rehearsal.py', 'current_outbox_rehearsal.py',
            'postgres_bootstrap_rehearsal.py'):
        shutil.copy2(root/'scripts'/name, target/name)
    for name in ('requirements-lab.txt', 's3_lab_backend.py'):
        shutil.copy2(root/'scripts/private-s3-rehearsal'/name, target/name)
    (target/'Dockerfile').write_text('''FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBUG=True PYTHON_DOTENV_DISABLED=1 REAL_EMAIL_ENABLED=False APPLICATION_EMAIL_ENABLED=False AJIRI_COMBINED_REHEARSAL=synthetic-only AJIRI_QUEUE_REHEARSAL=synthetic-only AJIRI_STORAGE_REHEARSAL=synthetic-only AJIRI_PRIVATE_STORAGE_REHEARSAL=synthetic-only
WORKDIR /app
COPY backend/requirements-prod.txt /app/requirements-prod.txt
COPY requirements-lab.txt /requirements-lab.txt
RUN python -m pip install --no-cache-dir -r requirements-prod.txt -r /requirements-lab.txt psycopg[binary]==3.3.6
COPY backend/ /app/
COPY s3_lab_backend.py /app/s3_lab_backend.py
COPY combined_recovery_rehearsal.py current_outbox_rehearsal.py postgres_bootstrap_rehearsal.py /
RUN mkdir -p /app/staticfiles && groupadd --gid 10001 ajiri-lab && useradd --no-log-init --uid 10001 --gid 10001 --no-create-home ajiri-lab
USER 10001:10001
CMD ["python", "/combined_recovery_rehearsal.py", "source"]
''')
    print(target)
