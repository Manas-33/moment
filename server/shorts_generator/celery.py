"""
Celery application for Moment.

Long-running video jobs (transcription, LLM highlight detection, cropping,
captioning, dubbing) run on a Celery worker backed by Redis instead of a raw
daemon thread inside the web process. This keeps requests non-blocking, survives
web restarts, and gives retries / time limits.

Local dev with no broker still works: the task launchers in shorts_api/tasks.py
fall back to a background thread unless USE_CELERY is enabled.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shorts_generator.settings")

app = Celery("moment")
# All CELERY_* settings in Django settings.py configure the app.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
