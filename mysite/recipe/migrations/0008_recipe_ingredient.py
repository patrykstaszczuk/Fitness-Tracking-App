# Generated by Django 3.1.7 on 2021-04-11 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0007_recipe_ingredient'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='ingredient',
            field=models.ManyToManyField(through='recipe.Recipe_Ingredient', to='recipe.Ingredient'),
        ),
    ]
