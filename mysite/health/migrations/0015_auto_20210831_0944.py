# Generated by Django 3.1.7 on 2021-08-31 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0014_auto_20210830_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1630403073.1168985),
        ),
    ]
