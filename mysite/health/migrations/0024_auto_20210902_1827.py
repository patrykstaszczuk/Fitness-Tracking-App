# Generated by Django 3.1.7 on 2021-09-02 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0023_auto_20210902_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1630607251.8808563),
        ),
    ]
