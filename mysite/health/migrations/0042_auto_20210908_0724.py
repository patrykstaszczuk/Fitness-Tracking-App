# Generated by Django 3.1.7 on 2021-09-08 07:24

from django.db import migrations, models
import time


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0041_auto_20210908_0722'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=time.time),
        ),
    ]
