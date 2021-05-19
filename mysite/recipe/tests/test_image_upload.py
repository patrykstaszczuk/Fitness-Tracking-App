import tempfile
import os

from PIL import Image

from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from django.urls import reverse


def image_upload_url(recipe_slug):
    """ return URL for recipe image upload """
    return reverse('recipe:recipe-upload-image', args=[recipe_slug, ])


class PrivateTestCases(TestCase):
    """ test image uploading scenarios """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpassword',
            name='test',
            age=25,
            sex='Male'
        )
        self.client.force_authenticate(user=self.user)

        defaults = {
            'name': 'Danie testowe',
            'calories': 1000,
            'prepare_time': 50,
            'portions': 4,
            'description': "Opis dania testowego"
        }
        self.sample_recipe = models.Recipe.objects.create(user=self.user,
                                                          **defaults)
    def tearDown(self):
        self.sample_recipe.photo1.delete()
        self.sample_recipe.photo2.delete()
        self.sample_recipe.photo3.delete()

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """ test that image is saved in the correct location """
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(self.sample_recipe,
                                                  'myimage.jpg')

        exp_path = f'recipes/{self.user.name}/{self.sample_recipe.slug}/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)

    def test_upload_image_to_recipe(self):
        """ test uploading an image to recipe """
        url = image_upload_url(self.sample_recipe.slug)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.post(url, {'photo1': ntf}, format='multipart')
        self.sample_recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('photo1', res.data)
        self.assertTrue(os.path.exists(self.sample_recipe.photo1.path))

    def test_upload_image_bad_request(self):
        """ test uploading an invalid image """
        url = image_upload_url(self.sample_recipe.slug)
        res = self.client.post(url, {'photo1': 'notimage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_multi_images_to_recipe(self):
        """ test uploading multi images to recipe """
        url = image_upload_url(self.sample_recipe.slug)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf, tempfile.NamedTemporaryFile(suffix='.jpg') as ntf2, tempfile.NamedTemporaryFile(suffix='.jpg') as ntf3:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            img.save(ntf2, format='JPEG')
            img.save(ntf3, format='JPEG')
            ntf.seek(0)
            ntf2.seek(0)
            ntf3.seek(0)
            res = self.client.post(url,
                                   {'photo1': ntf,
                                    'photo2': ntf2,
                                    'photo3': ntf3}, format='multipart')
        self.sample_recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('photo1', res.data)
        self.assertIn('photo2', res.data)
        self.assertIn('photo3', res.data)
        self.assertTrue(os.path.exists(self.sample_recipe.photo1.path))
        self.assertTrue(os.path.exists(self.sample_recipe.photo2.path))
        self.assertTrue(os.path.exists(self.sample_recipe.photo3.path))

    def test_deleting_images_when_recipe_is_deleted(self):
        """ test deleting all images from media folder relating to deleted
        recipe """

        url = image_upload_url(self.sample_recipe.slug)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.post(url, {'photo1': ntf}, format='multipart')

        self.sample_recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('photo1', res.data)
        self.assertTrue(os.path.exists(self.sample_recipe.photo1.path))
        path = str(self.sample_recipe.photo1)
        self.sample_recipe.delete()

        self.assertFalse(os.path.exists(path))

    def test_deleteting_images_when_recipe_is_updating(self):
        """ test deleting curenlty used image, in case of image replacement """

        url = image_upload_url(self.sample_recipe.slug)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf, tempfile.NamedTemporaryFile(suffix='.jpg') as ntf2:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            img.save(ntf2, format='JPEG')
            ntf.seek(0)
            ntf2.seek(0)

            res = self.client.post(url, {'photo3': ntf}, format='multipart')
            self.sample_recipe.refresh_from_db()
            self.assertIn('photo3', res.data)
            ntf_filepath = self.sample_recipe.photo3.path

            res = self.client.post(url, {'photo3': ntf2}, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.sample_recipe.refresh_from_db()
            self.assertTrue(os.path.exists(self.sample_recipe.photo3.path))
            self.assertFalse(os.path.exists(ntf_filepath))

    def test_new_image_upload_to_recipe(self):
        """ test if new image is upload properly and old image is no deleted"""

        url = image_upload_url(self.sample_recipe.slug)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf, tempfile.NamedTemporaryFile(suffix='.jpg') as ntf2:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            img.save(ntf2, format='JPEG')
            ntf.seek(0)
            ntf2.seek(0)

            res = self.client.post(url, {'photo1': ntf}, format='multipart')

            res = self.client.post(url, {'photo2': ntf2}, format='multipart')
            self.sample_recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('photo1', res.data)
            self.assertIn('photo2', res.data)
