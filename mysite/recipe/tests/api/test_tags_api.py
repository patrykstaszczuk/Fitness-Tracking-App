from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

TAG_CREATE = reverse('recipe:tag-create')


def tag_detail_url(slug: str) -> str:
    return reverse('recipe:tag-detail', kwargs={'slug': slug})


class TagApiTests(TestCase):

    def setUp(self):
        self.auth_user = get_user_model().objects.create_user(
            email='auth@gmail.com',
            name='auth',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client = APIClient()
        self.client.force_authenticate(self.auth_user)

    def _create_tag(self, name: str = 'tag') -> dict:
        payload = {
            'name': 'tag'
        }
        res = self.client.post(TAG_CREATE, payload)
        url = res._headers['location'][1]
        res = self.client.get(url)
        return res.data

    def test_unauthenticated_user_return_401(self) -> None:
        unauth_user = APIClient()
        res = unauth_user.post(TAG_CREATE, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_success(self) -> None:
        payload = {
            'name': 'tag'
        }
        res = self.client.post(TAG_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res._headers['location'][1])

    def test_update_tag_success(self) -> None:
        tag = self._create_tag()
        payload = {
            'name': 'new name'
        }
        res = self.client.put(tag_detail_url(tag['slug']), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['name'], payload['name'])

    def test_delete_tag_succes(self) -> None:
        tag = self._create_tag()
        res = self.client.delete(tag_detail_url(tag['slug']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
