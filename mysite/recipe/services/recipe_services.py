from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
from dataclasses import dataclass
from recipe.models import Recipe, Recipe_Ingredient
from recipe import selectors
from django.core.exceptions import ValidationError


@dataclass
class CreateRecipeDto:
    user: get_user_model
    name: str
    portions: int
    prepare_time: int
    description: str

    def __post_init__(self):
        self.slug = slugify(self.name)
        number_of_repeared_names = Recipe.objects.filter(
            user=self.user, name=self.name).count()
        if number_of_repeared_names > 0:
            self.slug += str(number_of_repeared_names + 1)


class CreateRecipe:
    def create(self, dto: CreateRecipeDto) -> None:
        return Recipe.objects.create(
            user=dto.user,
            name=dto.name,
            slug=dto.slug,
            portions=dto.portions,
            prepare_time=dto.prepare_time,
            description=dto.description
        )


class UpdateRecipe:
    def update(self, recipe: Recipe, dto: CreateRecipeDto) -> Recipe:
        for attr in vars(dto):
            setattr(recipe, attr, getattr(dto, attr))
        recipe.save()
        return recipe


@dataclass
class AddingTagsInputDto:
    user: get_user_model
    tag_ids: list[int]

    def __post_init__(self):
        user_tags = selectors.tag_list(self.user).values_list('id', flat=True)
        for tag_id in self.tag_ids:
            if tag_id not in user_tags:
                raise ValidationError(f'Tag with id: {tag_id} not exists')


class AddTagsToRecipe:
    def add(self, recipe: Recipe, dto: AddingTagsInputDto) -> None:
        recipe.tags.add(*dto.tag_ids)


@dataclass
class RemoveTagsInputDto:
    tag_ids: list[int]


class RemoveTagsFromRecipe:
    def remove(self, recipe: Recipe, dto: AddingTagsInputDto) -> None:
        recipe.tags.clear(*dto.tag_ids)


@dataclass
class RecipeIngredientServiceDto:
    ingredient_id = int
    unit_id = int
    amount = int

    user: get_user_model
    recipe: Recipe
    ingredients: list[ingredient_id, unit_id, amount]

    def __post_init__(self):
        pass


class AddIngredientsToRecipe:
    def add(self, dto: RecipeIngredientServiceDto) -> None:
        recipe = dto.recipe
        for item in dto.ingredients:
            recipe.ingredients.add(item['ingredient'],
                                   through_defaults={"unit_id": item['unit'],
                                                     "amount": item['amount']})


class RemoveIngredientsFromRecipe:
    def remove(self, dto: RecipeIngredientServiceDto) -> None:
        pass


@dataclass
class UpdateRecipeIngredientDto:
    recipe_ingredient: Recipe_Ingredient
    unit_id: int
    amount: int

    def __post_init__(self):
        pass


class UpdateRecipeIngredient:
    def update(self, dto: UpdateRecipeIngredientDto) -> None:
        recipe_ingredient = dto.recipe_ingredient
        recipe_ingredient.unit_id = dto.unit_id
        recipe_ingredient.amount = dto.amount
        recipe_ingredient.save()


class DeleteRecipe:
    def delete(self, recipe: Recipe) -> None:
        recipe.delete()
