# Generated by Django 3.1.7 on 2021-06-10 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0025_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='short_name',
            field=models.CharField(default='ml', max_length=10),
            preserve_default=False,
        ),
    ]