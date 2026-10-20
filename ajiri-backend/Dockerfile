FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt requirements-prod.txt ./
RUN python -m pip install -r requirements.txt \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin ajiri \
    && mkdir -p /app/staticfiles /data/private-media \
    && chown -R 10001:10001 /app/staticfiles /data \
    && chmod 700 /data /data/private-media
COPY manage.py ./
COPY accounts ./accounts
COPY config ./config
COPY jobs ./jobs
COPY profiles ./profiles
COPY scripts ./scripts
COPY frontend_build ./frontend_build
USER 10001:10001
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
