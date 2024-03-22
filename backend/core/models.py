from django.contrib.auth.models import User
from django.db import models


class ProcessStatus(models.IntegerChoices):
    SUCCESSFUL = 0, "Successful"
    PENDING = 1, "Pending"
    RUNNING = 2, "Running"
    STOPPING = 3, "Stopping"
    STOPPED = 4, "Stopped"
    FAILED = 5, "Failed"


class Process(models.Model):
    pipeline = models.CharField(max_length=255)
    pipeline_version = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    used_config = models.JSONField(null=True, blank=True, default=dict)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="processes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    executor = models.CharField(max_length=255, default="local")
    worker = models.CharField(max_length=255, null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    pid = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(
        verbose_name="Status",
        default=ProcessStatus.PENDING,
        choices=ProcessStatus.choices,
    )
    path = models.FilePathField(
        verbose_name="Path", null=True, blank=True, default=None
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.pipeline}-{str(self.pk).zfill(8)}"
