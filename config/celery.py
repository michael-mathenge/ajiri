import os
from celery import Celery

"""Setting up Celery — three pieces need to connectCelery needs: 
(1) a config file telling it how to find your Django project, 
(2) settings telling it where Redis lives, and 
(3) your ingestion function wrapped as an actual "task" Celery can schedule and run."""

"""os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') — Celery runs as its own separate process, not through manage.py — so it needs to be told explicitly where your Django settings live, since it won't discover this automatically the way Django's own commands do.
app.config_from_object('django.conf:settings', namespace='CELERY') — tells Celery "look inside settings.py for any setting name starting with CELERY_" — this is how we'll configure Redis as the broker in step 2, without needing a separate Celery-specific config file.
app.autodiscover_tasks() — tells Celery to automatically look inside every installed app (accounts, profiles, jobs, etc.) for a file called tasks.py, and register anything it finds. This is how your job-ingestion task will get picked up without manually registering it anywhere."""
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ajiri')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()