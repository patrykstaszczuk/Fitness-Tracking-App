# Generated by Django 3.1.7 on 2021-04-10 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0003_auto_20210410_0804'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='type',
        ),
        migrations.AddField(
            model_name='ingredient',
            name='tag',
            field=models.ManyToManyField(to='recipe.Tag'),
        ),
    ]
