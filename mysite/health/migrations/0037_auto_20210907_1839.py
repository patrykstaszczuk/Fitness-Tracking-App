# Generated by Django 3.1.7 on 2021-09-07 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0036_auto_20210904_1802'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1631039964.4966147),
        ),
    ]