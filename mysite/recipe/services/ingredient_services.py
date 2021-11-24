from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
from recipe.models import Ingredient
from django.core.exceptions import ValidationError
from dataclasses import dataclass
from recipe import selectors


@dataclass
class CreateIngredientServiceDto:
    user: get_user_model
    ready_meal: bool
    name: str
    calories: float
    proteins: float
    carbohydrates: float
    fats: float
    type: str
    fiber: float
    sodium: float
    potassium: float
    calcium: float
    iron: float
    magnesium: float
    selenium: float
    zinc: float

    def __post_init__(self):
        if self.name is None:
            raise ValidationError('Name is required for ingredient')


class UpdateIngredientServiceDto(CreateIngredientServiceDto):
    def __post_init__(self):
        pass


class CreateIngredient:
    def create(self, dto: CreateIngredientServiceDto) -> Ingredient:
        ready_meal = dto.ready_meal
        slug = slugify(dto.name)
        try:
            return Ingredient.objects.create(
                user=dto.user,
                name=dto.name,
                slug=slug,
                calories=dto.calories,
                proteins=dto.proteins,
                carbohydrates=dto.carbohydrates,
                fats=dto.fats,
                type=dto.type,
                fiber=dto.fiber,
                sodium=dto.sodium,
                potassium=dto.potassium,
                calcium=dto.calcium,
                iron=dto.iron,
                magnesium=dto.magnesium,
                selenium=dto.selenium,
                zinc=dto.zinc
            )
        except IntegrityError:
            raise ValidationError(
                f'Ingredient with name {dto.name} already exists')


class UpdateIngredient:
    def update(self, ingredient: Ingredient, dto: UpdateIngredientServiceDto) -> Ingredient:
        if dto.name is None:
            dto.name = ingredient.name
        slug = slugify(dto.name)
        for attr in vars(dto):
            setattr(ingredient, attr, getattr(dto, attr))
        try:
            ingredient.slug = slug
            ingredient.save()
        except IntegrityError:
            raise ValidationError(
                f'Ingredient with name {dto.name} already exists!')
        return ingredient


class DeleteIngredient:
    def delete(self, ingredient: Ingredient) -> None:
        ingredient.delete()


@dataclass
class AddingTagsInputDto:
    user: get_user_model
    tag_ids: list[int]

    def __post_init__(self):
        user_tags = selectors.tag_list(self.user).values_list('id', flat=True)
        for tag_id in self.tag_ids:
            if tag_id not in user_tags:
                raise ValidationError(f'Tag with id: {tag_id} not exists')


@dataclass
class RemoveTagsInputDto:
    tag_ids: list[int]


class AddTagsToIngredient:
    def add(self, ingredient: Ingredient, dto: AddingTagsInputDto) -> None:
        ingredient.tags.add(*dto.tag_ids)


class RemoveTagsFromIngredient:
    def remove(self, ingredient, dto: RemoveTagsInputDto) -> None:
        ingredient.tags.clear(*dto.tag_ids)


@dataclass
class MappingUnitDto:
    unit_id: int
    grams: int

    def __post_init__(self):
        pass


class MapUnitToIngredient:
    def map(self, ingredient: Ingredient, dto: MappingUnitDto) -> None:
        ingredient.unit.add(dto.unit_id, through_defaults={'grams': dto.grams})
