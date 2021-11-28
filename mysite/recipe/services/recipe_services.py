from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
from dataclasses import dataclass, fields, MISSING
from recipe.models import Recipe, Recipe_Ingredient
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
    ingredient_id = int
    unit_id = int
    amount = int

    user: get_user_model
    ingredients: list[dict[str, ingredient_id | unit_id | amount]]

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


class RemoveIngredientsFromRecipe:
    def remove(self, recipe: Recipe, dto: RemoveIngredientsFromRecipeDto) -> None:
        recipe.ingredients.remove(*dto.ingredient_ids)


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
        recipe_ingredient.save()


class DeleteRecipe:
    def delete(self, recipe: Recipe) -> None:
        recipe.delete()
