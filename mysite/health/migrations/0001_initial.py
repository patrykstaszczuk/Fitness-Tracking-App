# Generated by Django 3.1.7 on 2021-05-26 11:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthDiary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('weight', models.PositiveSmallIntegerField(default=0)),
                ('sleep_length', models.PositiveSmallIntegerField(default=0)),
                ('calories', models.PositiveIntegerField(default=0)),
                ('daily_thoughts', models.TextField(max_length=2000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]