# Generated by Django 3.1.7 on 2021-07-20 16:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0049_auto_20210714_0927'),
        ('meals_tracker', '0011_auto_20210719_1635'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngredientAmount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField()),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipe.ingredient')),
                ('meal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='meals_tracker.meal')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipe.unit')),
            ],
        ),
        migrations.AddField(
            model_name='meal',
            name='ingredient',
            field=models.ManyToManyField(blank=True, null=True, through='meals_tracker.IngredientAmount', to='recipe.Ingredient'),
        ),
    ]
