# Generated by Django 3.1.7 on 2021-05-10 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0021_auto_20210506_0742'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredient',
            name='_usage_counter',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
