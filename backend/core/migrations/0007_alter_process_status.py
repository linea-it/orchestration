# Generated by Django 5.0.3 on 2024-03-20 18:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_process_pid_alter_process_task_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="process",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "Successful"),
                    (1, "Pending"),
                    (2, "Running"),
                    (3, "Revoking"),
                    (4, "Revoked"),
                    (5, "Failed"),
                ],
                default=1,
                verbose_name="Status",
            ),
        ),
    ]
