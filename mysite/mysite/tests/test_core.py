from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status


class CoreApiTests(TestCase):
    """ test core app """

    def test_retrieve_api_root_links(self):
        """ test retrieving links to apps """

        self.client = APIClient()
        url = reverse('api_root')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
