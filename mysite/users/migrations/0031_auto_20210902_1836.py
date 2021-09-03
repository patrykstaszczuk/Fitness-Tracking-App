# Generated by Django 3.1.7 on 2021-09-02 18:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_auto_20210902_1829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stravaactivity',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stava_activity', to=settings.AUTH_USER_MODEL),
        ),
    ]
