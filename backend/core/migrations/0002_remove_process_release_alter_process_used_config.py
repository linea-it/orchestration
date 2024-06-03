# Generated by Django 5.0.3 on 2024-03-14 17:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="process",
            name="release",
        ),
        migrations.AlterField(
            model_name="process",
            name="used_config",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
