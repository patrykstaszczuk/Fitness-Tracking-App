# Generated by Django 3.1.7 on 2021-05-26 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0002_auto_20210526_1114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthdiary',
            name='sleep_length',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='healthdiary',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
