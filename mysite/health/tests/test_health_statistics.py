from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from users import serializers


class PrivateHealthApiTests(TestCase):
    """ TestCases for health testing """

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            age=25,
            height=188,
            weight=74,
            sex='Male'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_information(self):
        """ test retrieving information about user """

        url = reverse('users:profile')
        res = self.client.get(url)

        serializer = serializers.UserSerializer(self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_calculate_user_bmi(self):
        """ test calculating BMI based on user height and weight """

        url = reverse('health:bmi')

        res = self.client.get(url)
        bmi = self.user.get_bmi()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['bmi'], bmi)
