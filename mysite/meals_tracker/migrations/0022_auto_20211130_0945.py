# Generated by Django 3.1.7 on 2021-11-30 09:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meals_tracker', '0021_auto_20210724_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeportion',
            name='meal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_portion', to='meals_tracker.meal'),
        ),
    ]
