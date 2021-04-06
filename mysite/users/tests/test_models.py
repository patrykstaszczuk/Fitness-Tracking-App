from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):

    def test_create_user_with_email_successful(self):
        """ test creating a new user with an email is successful """

        email = "test@gmail.com"
        password = "testpass123"
        age = 25
        sex = 'MALE'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            age=age,
            sex=sex
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """ test the email for a new user is normalized """
        email = 'test@GMAIL.COM'
        password = 'testpass'
        age = 25
        sex = 'MALE'
        user = get_user_model().objects.create_user(email=email,
                                                    password=password,
                                                    age=age, sex=sex)
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """ test creating user with no email raises error """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email=None,
                                                 password="dada",
                                                 age=25, sex='Male')

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@gmail.com',
            password='teste',
            age=25,
            sex='Male'
        )

        self.assertTrue(user.is_superuser, True)
