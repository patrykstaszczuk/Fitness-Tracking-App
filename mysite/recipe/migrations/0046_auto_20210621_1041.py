# Generated by Django 3.1.7 on 2021-06-21 10:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0045_auto_20210621_1001'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ingredient_unit',
            unique_together=set(),
        ),
    ]
