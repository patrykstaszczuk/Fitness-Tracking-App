from .base_views import BaseViewClass
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework import status
from recipe import serializers, selectors
from recipe.models import Tag
from recipe.services import (
    CreateTag,
    CreateTagDto,
    DeleteTag,
    UpdateTag,
)


class BaseTagClass(BaseViewClass):
    def _set_location_in_header(self, request: Request, slug: str) -> dict:
        return {'Location': reverse(
                'recipe:tag-detail', request=request,
                kwargs={'slug': slug})}

    def _prepare_dto(self, request: Request) -> CreateTagDto:
        serializer = serializers.TagInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateTagDto(
            user=request.user,
            name=data['name']
        )

    def _get_object(self) -> Tag:
        """ return tag based on slug """
        slug = self.kwargs.get('slug')
        user = self.request.user
        return selectors.tag_get(user, slug)


class TagsApi(BaseTagClass):
    """ API for retreving and creating tags """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        user_tags = selectors.tag_list(user=request.user)
        serializer = serializers.TagOutputSerializer(user_tags, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ handling post request """

        dto = self._prepare_dto(request)
        service = CreateTag()
        tag = service.create(dto)
        headers = self._set_location_in_header(request, tag.slug)
        return Response(status=status.HTTP_201_CREATED, headers=headers)


class TagDetailApi(BaseTagClass):
    """ API for listing tags """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        user_tag = self._get_object()
        serializer = serializers.TagOutputSerializer(user_tag)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """ update tag """
        tag = self._get_object()
        dto = self._prepare_dto(request)
        service = UpdateTag()
        tag = service.update(tag, dto)
        headers = self._set_location_in_header(request, tag.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """ retrieve and delete tag """
        tag = self._get_object()
        service = DeleteTag()
        service.delete(tag)
        return Response(data=None, status=status.HTTP_204_NO_CONTENT)
