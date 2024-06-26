# Generated by Django 5.0.3 on 2024-05-09 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_process_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='status',
            field=models.IntegerField(choices=[(0, 'Successful'), (1, 'Pending'), (2, 'Running'), (3, 'Stopping'), (4, 'Stopped'), (5, 'Failed')], default=1, verbose_name='Status'),
        ),
    ]
