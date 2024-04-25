import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchestration.settings')

app = Celery('orchestration')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.task_routes = {
    "core.executors.local.tasks.*": {'queue': 'local'},
    "core.executors.slurm.tasks.*": {'queue': 'slurm'}
}

# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
app.conf.beat_schedule = {
    "slurm-check-finish": {
        "task": "core.executors.slurm.tasks.check_running_processes",
        "schedule": 30.0,
    },
}
app.conf.timezone = "UTC"

# Load task modules from all registered Django apps.
app.autodiscover_tasks(["core.executors.local", "core.executors.slurm"])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
