# Generated by Django 3.1.7 on 2021-11-28 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0060_auto_20211126_1152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='calcium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='fiber',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='iron',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='magnesium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='potassium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='selenium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='sodium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='zinc',
            field=models.FloatField(null=True),
        ),
    ]
