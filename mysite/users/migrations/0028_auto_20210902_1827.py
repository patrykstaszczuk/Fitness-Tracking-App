# Generated by Django 3.1.7 on 2021-09-02 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_stravaactivity_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stravaactivity',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
