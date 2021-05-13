# Generated by Django 3.1.7 on 2021-05-12 16:59

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_group_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='pending_membership',
            field=models.ManyToManyField(related_name='pending_membership', to=settings.AUTH_USER_MODEL),
        ),
    ]
