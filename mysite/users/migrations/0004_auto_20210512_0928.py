# Generated by Django 3.1.7 on 2021-05-12 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20210511_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]