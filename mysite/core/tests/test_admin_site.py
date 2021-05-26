from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='test@gmail.com',
            password='testpass',
            name='admin',
            age=25,
            height=188,
            weight=88,
            sex='Male'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create(
            email='test2@gmail.com',
            password='testpass',
            name='user',
            age=25,
            height=188,
            weight=88,
            sex='Male'
        )

    def test_users_listed(self):
        """ Test that user are listed on user page """
        url = reverse('admin:users_myuser_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """ Test that the user edit page works """
        url = reverse('admin:users_myuser_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """ test that the create user page works """
        url = reverse('admin:users_myuser_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
