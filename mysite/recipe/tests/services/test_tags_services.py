from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from recipe.models import Tag
from recipe.services import (
    CreateTag,
    CreateTagDto,
    UpdateTagDto,
    UpdateTag,
    DeleteTag,
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
    def _create_tag(user: get_user_model, name: str = 'test tag') -> Tag:
        return Tag.objects.create(user=user, name=name)

    def test_create_tag_success(self) -> None:
        dto = CreateTagDto(
            user=self.user,
            name='test'
        )
        service = CreateTag()
        tag = service.create(dto)
        self.assertEqual(tag.name, dto.name)

    def test_creating_tag_name_already_exists_failed(self) -> None:
        tag = self._create_tag(self.user)
        dto = CreateTagDto(
            user=self.user,
            name=tag.name
        )
        service = CreateTag()
        with self.assertRaises(ValidationError):
            service.create(dto)

    def test_updating_tag_success(self) -> None:
        tag = self._create_tag(self.user)
        dto = UpdateTagDto(name='new name')
        service = UpdateTag()
        tag = service.update(tag, dto)
        self.assertEqual(tag.name, dto.name)

    def test_updating_tag_name_exists_failed(self) -> None:
        tag = self._create_tag(self.user)
        tag2 = self._create_tag(self.user, name='tag2')
        dto = UpdateTagDto(name=tag.name)
        service = UpdateTag()
        with self.assertRaises(ValidationError):
            service.update(tag2, dto)

    def test_deleting_tag_success(self) -> None:
        tag = self._create_tag(self.user)
        service = DeleteTag()
        service.delete(tag)
        with self.assertRaises(Tag.DoesNotExist):
            tag.refresh_from_db()
