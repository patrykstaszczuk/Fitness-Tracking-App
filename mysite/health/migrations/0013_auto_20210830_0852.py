# Generated by Django 3.1.7 on 2021-08-30 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0012_healthdiary_last_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='last_update',
            field=models.PositiveIntegerField(default=1630313568.7664132),
        ),
    ]
