from django.contrib.auth import get_user_model
from django.utils.text import slugify
from unidecode import unidecode
from django.db import IntegrityError
from recipe.models import Ingredient
from django.core.exceptions import ValidationError
from dataclasses import dataclass, fields
from recipe import selectors
from recipe.services.tag_services import CreateTagDto, CreateTag


@dataclass
class CreateIngredientDto:
    user: get_user_model
    name: str = None
    ready_meal: bool = None
    calories: float = None
    proteins: float = None
    carbohydrates: float = None
    fats: float = None
    type: str = None
    fiber: float = None
    sodium: float = None
    potassium: float = None
    calcium: float = None
    iron: float = None
    magnesium: float = None
    selenium: float = None
    zinc: float = None

    def __post_init__(self):
        if self.name is None:
            raise ValidationError('Name is required for ingredient')
        fields_with_types = [(field.name, field.type)
                             for field in fields(CreateIngredientDto)]
        for field, type in fields_with_types:
            if type in [float, int]:
                value = getattr(self, field)
                if value is not None and value < 0:
                    raise ValidationError(
                        f'Value for field {field} cannot be negative!')
            continue


class UpdateIngredientDto(CreateIngredientDto):
    def __post_init__(self):
        pass


class CreateIngredient:
    def create(self, dto: CreateIngredientDto) -> Ingredient:

        slug = slugify(unidecode(dto.name)) + \
            '-user-' + str(dto.user.id)
        try:
            self.ingredient = Ingredient.objects.create(
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
                f'Ingredient with name "{dto.name}" already exists')
        if dto.ready_meal:
            self._add_ready_meal_tag()
        self._add_default_unit()

        return self.ingredient

    def _add_ready_meal_tag(self) -> None:
        tag = selectors.tag_ready_meal_get_or_create(self.ingredient.user)
        self.ingredient.tags.add(tag)

    def _add_default_unit(self) -> None:
        unit = selectors.unit_get_default()
        self.ingredient.units.add(unit, through_defaults={
                                  'grams_in_one_unit': 100})


class UpdateIngredient:
    def update(self, ingredient: Ingredient, dto: UpdateIngredientDto) -> Ingredient:
        if dto.name is None:
            dto.name = ingredient.name
            slug = ingredient.slug
        else:
            slug = slugify(unidecode(dto.name)) + \
                '-user-' + str(dto.user.id)
        for attr in vars(dto):
            setattr(ingredient, attr, getattr(dto, attr))
        try:
            ingredient.slug = slug
            ingredient.save()
        except IntegrityError:
            raise ValidationError(
                f'Ingredient with name "{dto.name}" already exists!')
        return ingredient


class DeleteIngredient:
    def delete(self, ingredient: Ingredient) -> None:
        ingredient.delete()


@dataclass
class AddingTagsToIngredientDto:
    user: get_user_model
    tag_ids: list[int]

    def __post_init__(self):
        user_tags = selectors.tag_list(self.user).values_list('id', flat=True)
        for tag_id in self.tag_ids:
            if tag_id not in user_tags:
                raise ValidationError(f'Tag with id: {tag_id} not exists')


@dataclass
class RemoveTagsFromIngredientDto:
    tag_ids: list[int]


class AddTagsToIngredient:
    def add(self, ingredient: Ingredient, dto: AddingTagsToIngredientDto) -> None:
        ingredient.tags.add(*dto.tag_ids)


class RemoveTagsFromIngredient:
    def remove(self, ingredient, dto: RemoveTagsFromIngredientDto) -> None:
        ingredient.tags.remove(*dto.tag_ids)


@dataclass
class MappingUnitDto:
    unit_id: int
    grams_in_one_unit: int


class MapUnitToIngredient:
    def map(self, ingredient: Ingredient, dto: MappingUnitDto) -> None:
        try:
            ingredient.units.add(dto.unit_id, through_defaults={
                                 'grams_in_one_unit': dto.grams_in_one_unit})
        except IntegrityError:
            raise ValidationError(
                f'Unit with if "{dto.unit_id}" does not exists!')
