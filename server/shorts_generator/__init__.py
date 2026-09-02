# Load the Celery app when Django starts so shared_task uses it. Guarded so the
# project still boots if celery is not installed (zero-dependency local runs).
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except Exception:
    celery_app = None
