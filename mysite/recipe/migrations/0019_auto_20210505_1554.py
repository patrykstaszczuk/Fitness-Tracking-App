# Generated by Django 3.1.7 on 2021-05-05 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0018_auto_20210505_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
