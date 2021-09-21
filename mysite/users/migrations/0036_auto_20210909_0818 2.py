# Generated by Django 3.1.7 on 2021-09-09 08:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_merge_20210909_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='founder',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='own_group', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='gender',
            field=models.CharField(choices=[('Male', 'M'), ('Female', 'F')], default='M', max_length=6),
        ),
    ]
