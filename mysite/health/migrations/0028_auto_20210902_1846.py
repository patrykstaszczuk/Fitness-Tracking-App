# Generated by Django 3.1.7 on 2021-09-02 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0027_auto_20210902_1836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1630608415.2880514),
        ),
    ]
