FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBUG=True PYTHON_DOTENV_DISABLED=1 REAL_EMAIL_ENABLED=False APPLICATION_EMAIL_ENABLED=False AJIRI_PRIVATE_STORAGE_REHEARSAL=synthetic-only
WORKDIR /app
COPY backend/requirements-prod.txt /app/requirements-prod.txt
COPY requirements-lab.txt /requirements-lab.txt
RUN python -m pip install --no-cache-dir -r requirements-prod.txt -r /requirements-lab.txt
COPY backend/ /app/
COPY s3_lab_backend.py /app/s3_lab_backend.py
COPY rehearsal.py /rehearsal.py
RUN mkdir -p /app/staticfiles
USER 10001:10001
CMD ["python", "/rehearsal.py"]
