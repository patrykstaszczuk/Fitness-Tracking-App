from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
from dataclasses import dataclass, fields, MISSING
from recipe.models import Recipe, Recipe_Ingredient, Ingredient_Unit
from recipe import selectors
from django.core.exceptions import ValidationError
from abc import ABC, abstractmethod


@dataclass
class CreateRecipeDto:
    user: get_user_model
    name: str = None
    portions: int = None
    prepare_time: int = None
    description: str = None

    def __post_init__(self):
        if self.name is None:
            raise ValidationError('Name is required for recipe')
        if self.portions is None or self.portions < 1:
            raise ValidationError(
                'Recipe must have at least one portion')
        if self.prepare_time is None or self.prepare_time < 0:
            raise ValidationError(
                'Prepare time must be set and cannot be negative')


class CreateRecipe:
    def create(self, dto: CreateRecipeDto) -> None:
        slug = slugify(dto.name)
        number_of_repeared_names = Recipe.objects.filter(
            user=dto.user, name=dto.name).count()
        if number_of_repeared_names > 0:
            slug += str(number_of_repeared_names + 1)

        return Recipe.objects.create(
            user=dto.user,
            name=dto.name,
            slug=slug,
            portions=dto.portions,
            prepare_time=dto.prepare_time,
            description=dto.description
        )


class UpdateRecipe:
    def update(self, recipe: Recipe, dto: CreateRecipeDto) -> Recipe:
        for attr in vars(dto):
            value = getattr(dto, attr)
            if value is not None:
                setattr(recipe, attr, getattr(dto, attr))
        if recipe.name != dto.name:
            slug = slugify(dto.name)
            number_of_repeared_names = Recipe.objects.filter(
                user=dto.user, name=dto.name).count()
            if number_of_repeared_names > 0:
                slug += str(number_of_repeared_names + 1)
            recipe.slug = slug
        recipe.save()
        return recipe


@dataclass
class AddingTagsToRecipeInputDto:
    user: get_user_model
    tag_ids: list[int]

    def __post_init__(self):
        user_tags = selectors.tag_list(self.user).values_list('id', flat=True)
        for tag_id in self.tag_ids:
            if tag_id not in user_tags:
                raise ValidationError(f'Tag with id: {tag_id} not exists')


class AddTagsToRecipe:
    def add(self, recipe: Recipe, dto: AddingTagsToRecipeInputDto) -> None:
        recipe.tags.add(*dto.tag_ids)


@dataclass
class RemoveTagsFromRecipeInputDto:
    tag_ids: list[int]


class RemoveTagsFromRecipe:
    def remove(self, recipe: Recipe, dto: AddingTagsToRecipeInputDto) -> None:
        recipe.tags.remove(*dto.tag_ids)


@dataclass
class AddIngredientsToRecipeDto:
    ingredient = int
    unit = int
    amount = int

    user: get_user_model
    ingredients: list[dict[str, ingredient | unit | amount]]

    def __post_init__(self):
        if self.ingredients is None:
            raise ValidationError('Provide list of ingredients for recipe')
        for item in self.ingredients:
            if not selectors.ingredient_is_mapped_with_unit(
                unit_id=item['unit'],
                ingredient_id=item['ingredient']
            ):
                raise ValidationError(
                    f'{item["ingredient"]} is not mapped with unit {item["unit"]}')


@dataclass
class RemoveIngredientsFromRecipeDto:
    ingredient_ids: list[int]


class AddIngredientsToRecipe:
    def add(self, recipe: Recipe, dto: AddIngredientsToRecipeDto) -> None:
        for item in dto.ingredients:
            recipe.ingredients.add(item['ingredient'],
                                   through_defaults={"unit_id": item['unit'],
                                                     "amount": item['amount']})

        service_dto = RecalculateRecipeCaloriesDto(
            ingredients_ids=[item['ingredient'] for item in dto.ingredients]
        )
        service = RecalculateRecipeCalories()
        service.add(service_dto, recipe)
        recipe.save()


class RemoveIngredientsFromRecipe:
    def remove(self, recipe: Recipe, dto: RemoveIngredientsFromRecipeDto) -> None:
        service_dto = RecalculateRecipeCaloriesDto(dto.ingredient_ids)
        service = RecalculateRecipeCalories()
        service.remove(service_dto, recipe)
        recipe.ingredients.remove(*dto.ingredient_ids)
        recipe.save()


@dataclass
class UpdateRecipeIngredientDto:
    ingredient_id: int
    unit_id: int
    amount: int

    def __post_init__(self):
        if not selectors.ingredient_is_mapped_with_unit(
            unit_id=self.unit_id,
            ingredient_id=self.ingredient_id
        ):
            raise ValidationError(
                f'{self.ingredient_id} is not mapped with unit {self.unit_id}')


class UpdateRecipeIngredient:
    def update(self, recipe_ingredient: Recipe_Ingredient, dto: UpdateRecipeIngredientDto) -> None:
        recipe_ingredient.unit_id = dto.unit_id
        recipe_ingredient.amount = dto.amount

        dto = RecalculateRecipeCaloriesDto(
            ingredients_ids=[recipe_ingredient.ingredient.id, ]
        )
        service = RecalculateRecipeCalories()
        service.remove(dto, recipe_ingredient.recipe)

        recipe_ingredient.save()

        service.add(dto, recipe_ingredient.recipe)
        recipe_ingredient.recipe.save()


class DeleteRecipe:
    def delete(self, recipe: Recipe) -> None:
        recipe.delete()


@dataclass
class RecalculateRecipeCaloriesDto:
    ingredients_ids: list[int]


class RecalculateRecipeCalories:

    def add(self, dto: RecalculateRecipeCaloriesDto, recipe: Recipe) -> None:
        """ add new ingredient calories to recipe """
        calories = self._sum_of_calories(dto, recipe)
        recipe.calories += calories

    def remove(self, dto: RecalculateRecipeCaloriesDto, recipe: Recipe) -> None:
        """ substract removed ingredients calories from recipe """
        calories = self._sum_of_calories(dto, recipe)
        recipe.calories -= calories

    def batch_removal(self, dto: RecalculateRecipeCaloriesDto, recipes: list[Recipe]) -> None:
        """ substract calories from recipes during Ingredient object update """
        for recipe in recipes:
            self.remove(dto, recipe)
            recipe.save()

    def batch_addition(self, dto: RecalculateRecipeCaloriesDto, recipes: list[Recipe]) -> None:
        """ add calories from recipes during Ingredient object update """
        for recipe in recipes:
            self.add(dto, recipe)
            recipe.save()

    def _sum_of_calories(self, dto: RecalculateRecipeCaloriesDto, recipe: Recipe) -> int:
        ingredient_quantity_items = Recipe_Ingredient.objects.filter(
            recipe=recipe, ingredient_id__in=dto.ingredients_ids).prefetch_related('ingredient', 'ingredient__ingredient_unit_set')
        calories = 0
        for item in ingredient_quantity_items:
            calories += selectors.ingredient_calculate_calories(
                ingredient=item.ingredient,
                unit=item.unit,
                amount=item.amount,
                )
            # try:
            #     mapped_unit_grammage = item.ingredient.ingredient_unit_set.get(
            #         unit_id=item.unit_id).grams_in_one_unit
            # except Ingredient_Unit.DoesNotExist:
            #     raise ValidationError(
            #         f'{item.ingredient} is not mapped with unit id {item.unit_id}')
            #
            # calories += item.ingredient.calories * \
            #     (item.amount//mapped_unit_grammage)
        return calories
