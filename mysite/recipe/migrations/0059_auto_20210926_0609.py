# Generated by Django 3.1.7 on 2021-09-26 06:09

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipe', '0058_merge_20210922_1153'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='recipe',
            unique_together={('user', 'name')},
        ),
    ]