# Generated by Django 3.1.7 on 2021-05-28 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0005_auto_20210528_0731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='calories',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='healthdiary',
            name='rest_heart_rate',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='healthdiary',
            name='sleep_length',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='healthdiary',
            name='weight',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
