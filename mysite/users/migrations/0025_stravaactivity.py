# Generated by Django 3.1.7 on 2021-09-02 11:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_auto_20210901_1307'),
    ]

    operations = [
        migrations.CreateModel(
            name='StravaActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strava_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('calories', models.PositiveIntegerField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stava_activity', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
