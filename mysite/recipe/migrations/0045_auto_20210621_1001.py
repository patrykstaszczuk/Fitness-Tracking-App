# Generated by Django 3.1.7 on 2021-06-21 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0044_auto_20210619_1043'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ingredient_unit',
            unique_together={('unit', 'ingredient')},
        ),
    ]
