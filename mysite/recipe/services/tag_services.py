from django.contrib.auth import get_user_model
from dataclasses import dataclass
from recipe.models import Tag
from django.utils.text import slugify
from django.db import IntegrityError
from django.core.exceptions import ValidationError


@dataclass
class CreateTagDto:
    user: get_user_model
    name: str

    def __post_init__(self):
        pass


class CreateTag:
    def create(self, dto: CreateTagDto) -> Tag:
        user = dto.user
        name = dto.name

        try:
            slug = slugify(name)
            return Tag.objects.create(user=user, name=name, slug=slug)
        except IntegrityError:
            raise ValidationError(f'Tag with name: {name} already exists')


@dataclass
class UpdateTagDto:
    name: str


class UpdateTag:
    def update(self, tag: Tag, dto: UpdateTagDto) -> Tag:
        name = dto.name
        slug = slugify(name)
        tag.name = name
        tag.slug = slug
        try:
            tag.save()
            return tag
        except IntegrityError:
            raise ValidationError(f'Tag with name: {name} already exists')


class DeleteTag:
    def delete(self, tag: Tag) -> None:
        tag.delete()
