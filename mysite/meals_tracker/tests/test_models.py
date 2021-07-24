from django.test import TestCase
from django.contrib.auth import get_user_model
from meals_tracker import models
from recipe.models import Recipe, Ingredient, Unit
import datetime


def sample_recipe(user, name='test', calories=0, **kwargs):
    """ create sample recipe """
    return Recipe.objects.create(
        user=user,
        name=name,
        calories=calories,
        **kwargs
    )


def sample_ingredient(**kwargs):
    return Ingredient.objects.create(
        **kwargs
    )


def sample_category(name='breakfast'):
    """ create sample category """
    return models.MealCategory.objects.create(name=name)


class MealModelTestCase(TestCase):
    """ tests for meal model """

    def setUp(self):
        self.user = get_user_model().objects.create(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            height=188,
            weight=85,
            age=25,
            gender='Male'
        )
        self.now = datetime.date.today()
        self.unit = Unit.objects.create(name='gram')
        self.category = sample_category()

    def test_meal_str(self):
        """ test string representation of meal model """

        meal = models.Meal.objects.create(user=self.user,
                                          category=sample_category(name='Supper'))

        self.assertEqual(str(meal), f'{meal.user} + {meal.date}')

    def test_auto_calories_calculation_based_on_recipe(self):
        """ test auto calories calculation from recipe """

        recipe = sample_recipe(user=self.user)

        meal = models.Meal.objects.create(user=self.user,
                                          category=sample_category(name='Supper'))
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        self.assertEqual(recipe.calories, meal.calories)

    def test_meal_category_str(self):
        """ test string representation of meal category """

        category = models.MealCategory.objects.create(name='Dinner')

        self.assertEqual(str(category), category.name)

    def test_retrieve_category_of_meal(self):
        """ test retreving category from field """

        breakfast = models.MealCategory.objects.create(name='Dinner')
        meal = models.Meal.objects.create(user=self.user, category=breakfast)

        self.assertEqual(breakfast, meal.category)

    def recalculate_calories_when_recipes_ingredient_changed(self):
        """ test recalculating meal calories when reicpes ingredients change"""
        ing = sample_ingredient(user=self.user, name='Coś', calories='1000')
        ing2 = sample_ingredient(user=self.user, name='Coś2', calories='2000')
        recipe = sample_recipe(user=self.user, portions=4)
        recipe.ingredients.add(ing, through_defaults={'unit': self.unit,
                                                      'amount': 100})
        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category,)
        meal.recipes.add(recipe, through_defaults={'portion': 1})

        self.assertEqual(meal.calories, 250)

        recipe.ingredients.remove(ing)
        recipe.ingredients.add(ing2, through_defaults={'amount': 100,
                                                       'unit': self.unit})
        meal.refresh_from_db()
        self.assertEqual(meal.calories, 500)

    def recalculate_calories_when_ingredient_updated(self):
        """ test recalculating meal calories when one of the ingredient
        assigned to recipe changed """

        ing = sample_ingredient(user=self.user, name='Coś', calories='1000')
        recipe = sample_recipe(user=self.user, portions=4)
        recipe.ingredients.add(ing, through_defaults={'unit': self.unit,
                                                      'amount': 100})
        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category,)
        meal.recipes.add(recipe, through_defaults={'portion': 1})

        self.assertEqual(meal.calories, 250)

        ing.calories = '2000'
        ing.save()
        meal.refresh_from_db()
        self.assertEqual(meal.calories, 500)
