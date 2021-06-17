# Generated by Django 3.1.7 on 2021-06-15 07:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0038_auto_20210615_0735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='calories',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0, 'Value must be greater then 0')]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='carbohydrates',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0, 'Value must be greater then 0')]),
        ),
    ]