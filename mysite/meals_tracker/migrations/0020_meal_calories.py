# Generated by Django 3.1.7 on 2021-07-23 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meals_tracker', '0019_remove_meal_calories'),
    ]

    operations = [
        migrations.AddField(
            model_name='meal',
            name='calories',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
    ]
