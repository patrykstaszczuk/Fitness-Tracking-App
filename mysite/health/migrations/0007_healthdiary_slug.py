# Generated by Django 3.1.7 on 2021-05-31 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0006_auto_20210528_0831'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthdiary',
            name='slug',
            field=models.SlugField(default='test'),
            preserve_default=False,
        ),
    ]
