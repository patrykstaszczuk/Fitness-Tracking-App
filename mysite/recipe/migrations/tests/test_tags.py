from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status

from recipe import models, services
from recipe import serializers


TAG_LIST_URL = reverse('recipe:tag-list')
TAG_CREATE_URL = reverse('recipe:tag-create')


def reverse_tag_update(slug):
    return reverse('recipe:tag-update', kwargs={'slug': slug})


def sample_user(email='user2@gmail.com', name='test2'):
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        weight=88,
        height=188,
        gender='Male'
    )


class PublicTagTestsApi(TestCase):
    """ test tags for unauthenticated user """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ test if unauthenticated user has no access to site """
        res = self.client.get(TAG_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """ test tags for authenticated user """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='test',
            password='testpass',
            age=25,
            weight=88,
            height=188,
            gender='Male'
        )
        self.client.force_authenticate(user=self.user)
        self.factory = APIRequestFactory()

    def test_retrieve_tags_success(self):
        """ retrieve all tags which are created by specific user """
        models.Tag.objects.create(name='Wegański', user=self.user)
        models.Tag.objects.create(name='Zupa', user=self.user)

        request = self.factory.get(TAG_LIST_URL)

        res = self.client.get(TAG_LIST_URL)
        tags = models.Tag.objects.filter(user=self.user)
        serializer = serializers.TagOutputSerializer(
            tags, many=True, context={'request': request})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertTrue(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """ test retrieve tags which are created by specific user """
        tag = services.tag_create(user=self.user, data={'name': 'Zupa'})

        user2 = sample_user()
        models.Tag.objects.create(name='Obiad', user=user2)

        res = self.client.get(TAG_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """ test create tag with success """
        payload = {
            'name': 'Nowy Tag',
            'user': self.user
        }
        res = self.client.post(TAG_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json()['data']['slug'], 'nowy-tag')

    def test_create_tag_name_too_long(self):
        """ test create tag with name too long """
        payload = {
            'name': 'nazwa jest zbyt dlug max 15 znakow',
            'user': self.user
        }
        res = self.client.post(TAG_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crate_tag_blank_name(self):
        """ test create tag with blank name error """
        payload = {
            'name': '',
            'user': self.user
        }
        res = self.client.post(TAG_CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_invalid_name(self):
        """ test creating tag with name which is already is db """
        services.tag_create(user=self.user, data={'name': 'nazwa'})

        payload = {
            'name': 'Nazwa',
            'user': self.user
        }
        res = self.client.post(TAG_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_by_different_user_success(self):
        """ test update tag with name which is already used but created
            by different user"""
        user2 = sample_user()
        services.tag_create(user=user2, data={'name': 'nazwa'})

        res = self.client.post(TAG_CREATE_URL, {'name': 'nazwa'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        tags = models.Tag.objects.all()
        self.assertEqual(len(tags), 2)

    def test_full_update_tag_success(self):
        """ test updating tag succes """
        tag = services.tag_create(user=self.user, data={'name': 'nazwa'})

        payload = {
            'name': 'new2345',
        }
        res = self.client.put(reverse_tag_update(tag.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotEqual(tag.name, payload['name'])

    def test_tag_update_if_name_not_change(self):
        """ test tag update if the name is not change """
        tag = services.tag_create(user=self.user, data={'name': 'nazwa'})
        payload = {
            'name': 'nazwa'
        }
        res = self.client.put(reverse_tag_update(tag.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_tag_success(self):
        tag = services.tag_create(user=self.user, data={'name': 'nazwa'})
        res = self.client.delete(reverse_tag_update(tag.slug), follow=True)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = models.Tag.objects.filter(id=tag.id).exists()

        self.assertFalse(tags)

    def test_delete_tag_only_for_requested_user(self):
        """ test that only tag for requested user is deleted """
        user2 = sample_user()
        tag = services.tag_create(user=self.user, data={'name': 'tag'})
        tag = services.tag_create(user=user2, data={'name': 'tag'})

        res = self.client.delete(reverse_tag_update(tag.slug))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = models.Tag.objects.all()
        self.assertEqual(len(tags), 1)