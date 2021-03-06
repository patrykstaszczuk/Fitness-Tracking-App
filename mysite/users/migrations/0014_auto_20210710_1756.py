# Generated by Django 3.1.7 on 2021-07-10 17:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_auto_20210710_0703'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='founder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='founder', to=settings.AUTH_USER_MODEL, unique=True),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='gender',
            field=models.CharField(choices=[('Male', 'M'), ('Female', 'F')], default='M', max_length=6),
        ),
    ]
