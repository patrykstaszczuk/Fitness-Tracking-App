# Generated by Django 3.1.7 on 2021-09-03 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0030_auto_20210903_0754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1630655853.6332707),
        ),
    ]
