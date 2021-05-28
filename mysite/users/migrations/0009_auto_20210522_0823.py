# Generated by Django 3.1.7 on 2021-05-22 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20210519_0806'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='height',
            field=models.PositiveSmallIntegerField(default=180),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='myuser',
            name='weight',
            field=models.PositiveSmallIntegerField(default=70),
            preserve_default=False,
        ),
    ]