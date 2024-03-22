# Generated by Django 5.0.3 on 2024-03-13 18:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Process",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("pipeline", models.CharField(max_length=255)),
                (
                    "pipeline_version",
                    models.CharField(
                        blank=True, default=None, max_length=255, null=True
                    ),
                ),
                ("used_config", models.JSONField(blank=True, null=True)),
                (
                    "release",
                    models.CharField(
                        blank=True, default=None, max_length=255, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("executor", models.CharField(default="local", max_length=255)),
                ("task_id", models.IntegerField(blank=True, null=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "Successful"),
                            (1, "Pending"),
                            (2, "Running"),
                            (3, "Revoked"),
                            (4, "Failed"),
                        ],
                        default=1,
                        verbose_name="Status",
                    ),
                ),
                (
                    "path",
                    models.FilePathField(
                        blank=True, default=None, null=True, verbose_name="Path"
                    ),
                ),
                ("comment", models.TextField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="processes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]