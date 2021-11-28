from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from recipe.models import Ingredient, Tag, Unit
from recipe.services import (
    CreateIngredientDto,
    CreateIngredient,
    UpdateIngredientDto,
    UpdateIngredient,
    DeleteIngredient,
    AddTagsToIngredient,
    AddingTagsToIngredientDto,
    RemoveTagsFromIngredient,
    RemoveTagsFromIngredientDto,
    MappingUnitDto,
    MapUnitToIngredient,
)


class IngredientServicesTests(TestCase):

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,
        )

    @staticmethod
    def _create_ingredient(user: get_user_model, name: str = 'ingredient') -> Ingredient:
        dto = CreateIngredientDto(
            user=user,
            name=name,
            calories=100,
        )
        return CreateIngredient().create(dto)

    @staticmethod
    def _create_tag(user: get_user_model, name: str = 'tag') -> Tag:
        return Tag.objects.create(user=user, name=name, slug=slugify(name))

    def test_create_ingredient_service(self) -> None:
        dto = CreateIngredientDto(
            user=self.user,
            name='test ingredient',
            calories=500,
        )
        service = CreateIngredient()
        ingredient = service.create(dto)

        self.assertEqual(ingredient.name, dto.name)

    def test_creating_ingredient_automatically_add_default_unit_to_it(self) -> None:
        dto = CreateIngredientDto(
            user=self.user,
            name='test ingredient',
            calories=500,
        )
        service = CreateIngredient()
        ingredient = service.create(dto)
        unit = Unit.objects.get(name='gram')
        self.assertEqual(ingredient.units.all()[0], unit)

    def test_creating_ingredient_with_same_name_as_other_user_ingredient_success(self) -> None:
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            name='testname2',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,
        )
        user2_ingredient = self._create_ingredient(user=user2)
        dto = CreateIngredientDto(
            user=self.user,
            name=user2_ingredient.name
        )
        service = CreateIngredient()
        ingredient = service.create(dto)
        self.assertEqual(ingredient.slug, user2_ingredient.name
                         + '-user-' + str(self.user.id))

    def test_automatically_add_ready_meal_tag_to_ingredient_if_set(self) -> None:
        dto = CreateIngredientDto(
            user=self.user,
            name='test ingredient',
            ready_meal=True,
            calories=500,
        )
        service = CreateIngredient()
        ingredient = service.create(dto)
        ready_meal_tag = Tag.objects.get(name='Ready Meal')
        self.assertEqual(ingredient.tags.all()[0].name, ready_meal_tag.name)

    def test_creating_ingredient_with_negative_value_failed(self) -> None:
        with self.assertRaises(ValidationError):
            CreateIngredientDto(
                user=self.user,
                name='test ingredient',
                calories=-500,
                potassium=-1
                 )

    def test_update_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        dto = UpdateIngredientDto(
            user=self.user,
            calories=1000
        )
        service = UpdateIngredient()
        ingredient = service.update(ingredient, dto)
        self.assertEqual(ingredient.calories, dto.calories)

    def test_updating_ingredient_with_already_taken_name_failed(self) -> None:
        ingredient1 = self._create_ingredient(self.user)
        ingredient2 = self._create_ingredient(self.user, name='ingredient2')
        dto = UpdateIngredientDto(
            user=self.user,
            name=ingredient1.name,
            sodium=100,
        )
        service = UpdateIngredient()
        with self.assertRaises(ValidationError):
            service.update(ingredient2, dto)

    def test_deleting_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        service = DeleteIngredient()
        service.delete(ingredient)
        with self.assertRaises(Ingredient.DoesNotExist):
            ingredient.refresh_from_db()

    def test_adding_tags_to_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        tag1 = self._create_tag(self.user)
        tag2 = self._create_tag(self.user, name='tag2')
        dto = AddingTagsToIngredientDto(
            user=self.user,
            tag_ids=[tag1.id, tag2.id]
        )
        service = AddTagsToIngredient()
        service.add(ingredient, dto)
        self.assertEqual(ingredient.tags.all().count(), 2)

    def test_adding_non_existins_tag_to_ingredient_failed(self) -> None:
        ingredient = self._create_ingredient(self.user)
        with self.assertRaises(ValidationError):
            AddingTagsToIngredientDto(
                user=self.user,
                tag_ids=[1, 2]
            )

    def test_removing_tags_from_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        tag1 = self._create_tag(self.user)
        tag2 = self._create_tag(self.user, name='tag2')
        ingredient.tags.add(tag1, tag2)
        dto = RemoveTagsFromIngredientDto(
            tag_ids=[tag2.id, ]
        )
        service = RemoveTagsFromIngredient()
        service.remove(ingredient, dto)
        self.assertEqual(ingredient.tags.all().count(), 1)

    def test_mapping_new_unit_to_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        unit = Unit.objects.create(name='test')
        dto = MappingUnitDto(
            unit_id=unit.id,
            grams_in_one_unit=100,
        )
        service = MapUnitToIngredient()
        service.map(ingredient, dto)
        self.assertEqual(ingredient.units.all().count(), 2)

    def test_mapping_non_existing_unit_to_ingredient_failed(self) -> None:
        ingredient = self._create_ingredient(self.user)
        dto = MappingUnitDto(
            unit_id=1,
            grams_in_one_unit=100,
        )
        service = MapUnitToIngredient()
        with self.assertRaises(ValidationError):
            service.map(ingredient, dto)
