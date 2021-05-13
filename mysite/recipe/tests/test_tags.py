from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.serializers import TagSerializer

from django.shortcuts import get_object_or_404

TAG_URL = reverse('recipe:tag-list')


def reverse_tag_detail(slug):
    return reverse('recipe:tag-detail', kwargs={'slug': slug})


class PublicTagTestsApi(TestCase):
    """ test tags for unauthenticated user """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ test if unauthenticated user has no access to site """
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagTestsApi(TestCase):
    """ test tags for authenticated user """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='test',
            password='testpass',
            age=25,
            sex='Male'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags_success(self):
        """ retrieve all tags which are created by specific user """
        models.Tag.objects.create(name='Wegański', user=self.user)
        models.Tag.objects.create(name='Zupa', user=self.user)

        res = self.client.get(TAG_URL)
        tags = models.Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertTrue(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """ test retrieve tags which are created by specific user """
        tag = models.Tag.objects.create(name='Zupa', user=self.user)

        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            name='test2',
            password='testpass',
            age=25,
            sex='Male'
        )
        models.Tag.objects.create(name='Obiad', user=user2)

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """ test create tag with success """
        payload = {
            'name': 'Nowy Tag',
            'user': self.user
        }
        res = self.client.post(TAG_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_tag_to_long(self):
        """ test create tag with name to long """
        payload = {
            'name': 'nazwa jest zbyt dlug max 15 znakow',
            'user': self.user
        }
        res = self.client.post(TAG_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crate_tag_blank_name(self):
        """ test create tag with blank name error """
        payload = {
            'name': '',
            'user': self.user
        }
        res = self.client.post(TAG_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_invalid_name(self):
        """ test creating tag with name which is already is db """
        models.Tag.objects.create(name='Nazwa', user=self.user)

        payload = {
            'name': 'Nazwa',
            'user': self.user
        }
        res = self.client.post(TAG_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_update_tag_success(self):
        """ test updating tag succes """
        tag = models.Tag.objects.create(name='nazwa', user=self.user)

        payload = {
            'name': 'new2345',
        }
        res = self.client.put(reverse_tag_detail(tag.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotEqual(tag.name, payload['name'])

    def test_tag_update_if_name_not_change(self):
        """ test tag update if the name is not change """
        tag = models.Tag.objects.create(name='nazwa', user=self.user)
        payload = {
            'name': 'nazwa'
        }
        res = self.client.put(reverse_tag_detail(tag.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_create_tag_for_different_user_success(self):
        """ test update tag with name which is already used but created
            by different user"""
        user2 = get_user_model().objects.create_user(
            email='user2@gmail.com',
            name='user2',
            password='testpass',
            age=25,
            sex='Male'
        )
        models.Tag.objects.create(name='nazwa', user=user2)

        res = self.client.post(TAG_URL, {'name': 'nazwa'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        tags = models.Tag.objects.all()
        self.assertEqual(len(tags), 2)

    def test_delete_tag_success(self):
        tag = models.Tag.objects.create(name='nazwa', user=self.user)

        res = self.client.delete(reverse_tag_detail(tag.slug))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = models.Tag.objects.filter(id=tag.id).exists()

        self.assertFalse(tags)

    def test_delete_tag_only_for_requested_user(self):
        """ test that only tag for requested user is deleted """
        user2 = get_user_model().objects.create_user(
            email='user2@gmail.com',
            name='user2',
            password='testpass',
            age=25,
            sex='Male'
        )
        tag = models.Tag.objects.create(name='tag', user=self.user)
        models.Tag.objects.create(name='tag', user=user2)

        res = self.client.delete(reverse_tag_detail(tag.slug))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = models.Tag.objects.all()
        self.assertEqual(len(tags), 1)
