# Generated by Django 3.1.7 on 2021-09-02 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_stravaactivity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stravaapi',
            old_name='last_update',
            new_name='last_request_epoc_time',
        ),
    ]