# Generated by Django 3.1.7 on 2021-06-15 07:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0040_auto_20210615_0740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='calcium',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='fats',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='fiber',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='iron',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='magnesium',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='potassium',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='proteins',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='selenium',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='sodium',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='zinc',
            field=models.FloatField(null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
