import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from users import selectors as user_selectors
from health import models
from recipe.models import Recipe, Unit, Ingredient
from meals_tracker.models import MealCategory, Meal
from unittest.mock import patch

HEALTH_DIARY = reverse('health:health-diary')
UPDATE_HEALTH_DIARY = reverse('health:health-diary-update')
HEALTH_RAPORT = reverse('health:health-raport-list')
WEEKLY_HEALTH_SUMMARY = reverse('health:weekly-summary')
# USER_HEALTH_STATISTIC_RAPORT = reverse('health:health-list')
# USER_HEALTH_STATISTIC_WEEKLY_SUMMARY = reverse('health:weekly-summary')


def user_health_statistics_detail(slug: str) -> str:
    """ generate url for retrieveing health statistics details """
    return reverse('health:health-raport-detail', kwargs={'slug': slug})


def user_health_statistic_sumamry(slug: str) -> str:
    """ generate url for retrieving specific health statistic summary """
    return reverse('health:health-statistic-history', kwargs={'slug': slug})


def user_health_statistic_update(slug: str) -> str:
    """ generate url for update post health statistics """
    return reverse('health:health-raport-update', kwargs={'slug': slug})


def sample_user(email='test2@gmail.com', name='test2'):
    """ creating sample user """
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        height=188,
        weight=74,
        gender='Male'
    )


def sample_meal(user, calories=1000):
    """ create and return meal object """
    recipe = Recipe.objects.create(
        user=user, name='test', slug='test', portions=4)
    unit = Unit.objects.create(name='gram')
    category = MealCategory.objects.create(name='breakfast')
    ingredient = Ingredient.objects.create(user=user, name='ing',
                                           calories=1000)
    recipe.ingredients.add(ingredient, through_defaults={"unit": unit,
                                                         "amount": 100})
    meal = Meal.objects.create(user=user, category=category)
    meal.recipes.add(recipe, through_defaults={"portion": 1})
    return meal


class HealthApiTests(TestCase):
    """ TestCases for health testing """

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            age=25,
            height=188,
            weight=74,
            gender='Male'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_calculate_user_bmi(self):

        url = reverse('health:bmi-get')

        res = self.client.get(url)
        bmi = user_selectors.get_bmi(user=self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['bmi'], bmi)

    def test_retrieve_user_daily_health_statistics(self):

        daily_data = models.HealthDiary.objects.create(
            user=self.user,
            weight=70,
            sleep_length='07:14:00'
        )

        res = self.client.get(HEALTH_DIARY)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['weight'], daily_data.weight)

    def test_retrieving_proper_calories_amount_based_on_meals(self):
        meal = sample_meal(user=self.user, calories=1000)
        res = self.client.get(HEALTH_DIARY)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['calories'], meal.calories)

    def test_create_user_daily_health_statistics(self):

        payload = {
            'weight': 74.3,
            'sleep_length': '07:24:00',
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.patch(UPDATE_HEALTH_DIARY, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['weight'], payload['weight'])
        self.assertEqual(res.data['sleep_length'], payload['sleep_length'])
        self.assertEqual(res.data['daily_thoughts'], payload['daily_thoughts'])

    def test_updating_user_daily_health_statistics_with_invalid_values(self):

        payload = {
            'sleep_length': '1000',
            'weight': '1000',
            'rest_heart_rate': '1000',
            'calories': '2000',
        }

        res = self.client.patch(UPDATE_HEALTH_DIARY, payload,
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_updating_user_diary_forbidden_fields_failed(self):
        payload = {
            'user': 'user2',
            'date': '2020-03-30'
        }

        res = self.client.patch(UPDATE_HEALTH_DIARY, payload,
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_updating_user_weight_with_null(self):

        diary = models.HealthDiary.objects.create(user=self.user, weight=74)

        payload = {
            'weight': None,
            'sleep_length': '7:00:00',
            'daily_thoughts': ''
            }
        res = self.client.patch(UPDATE_HEALTH_DIARY, payload,
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        diary.refresh_from_db()

    def test_retrieving_health_statistics_raport(self):

        diaries_list = []
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                                                              date='2021-05-27', weight=73.2))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                                                              date='2021-05-26', weight=73.2))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                                                              date='2021-05-25',))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                                                              date='2021-05-24', weight=73.2))

        res = self.client.get(HEALTH_RAPORT)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 4)

    def test_retrieving_health_statistics_raport_users_separation(self):
        user2 = sample_user()
        models.HealthDiary.objects.create(user=user2, date='2021-05-22')
        models.HealthDiary.objects.create(user=self.user, date='2021-05-22')
        models.HealthDiary.objects.create(user=self.user, date='2021-05-23')

        res = self.client.get(HEALTH_RAPORT)
        self.assertEqual(len(res.data), 2)

    def test_exclude_today_statistics_from_history(self):
        models.HealthDiary.objects.create(user=self.user, date='2021-05-25')
        models.HealthDiary.objects.create(user=self.user, date='2021-05-26')
        models.HealthDiary.objects.create(user=self.user)
        res = self.client.get(HEALTH_RAPORT)
        self.assertEqual(len(res.data), 2)

    def test_retrieving_health_statistic_detail(self):
        diary = models.HealthDiary.objects.create(user=self.user,
                                                  date=datetime.date(
                                                      2021, 5, 22),
                                                  weight=65)

        res = self.client.get(user_health_statistics_detail(diary.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['weight'], diary.weight)
        self.assertEqual(res.data['date'], str(diary.date))

    def test_retrieving_health_statistic_detail_users_separation(self):
        user2 = sample_user()

        models.HealthDiary.objects.create(user=user2, date='2021-05-30')
        diary = models.HealthDiary.objects.create(user=self.user,
                                                  date='2021-05-30')

        res = self.client.get(user_health_statistics_detail(diary.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_history_statistic_success(self):
        """ test updating history statistics """

        diary = models.HealthDiary.objects.create(user=self.user,
                                                  calories=1000,
                                                  date='2021-05-12')
        payload = {
            'weight': 74,
            'rest_heart_rate': None,
            'sleep_length': '5:00'
        }
        res = self.client.patch(user_health_statistic_update(diary.slug),
                                payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(payload['weight'], res.data['weight'])

    def test_retrieving_weekly_average_health_stats_for_user(self):
        """ test retrieving average stats for user """

        avg_weight = 0
        for i in range(1, 8):
            diary = models.HealthDiary.objects.create(
                user=self.user,
                weight=70+i,
                sleep_length='7:30:00',
                date=datetime.date.today() - datetime.timedelta(days=i)
            )
            avg_weight += diary.weight
        avg_weight = avg_weight/7

        res = self.client.get(WEEKLY_HEALTH_SUMMARY)
        self.assertEqual(res.data['weight'], avg_weight)

    def test_retrieving_weigth_history(self):

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                weight=70+i
            )
        res = self.client.get(user_health_statistic_sumamry('weigth'),
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

    def test_retrieving_sleep_length_history(self):

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length='7:00'
            )

        res = self.client.get(user_health_statistic_sumamry('sleep_length'),
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

    def test_retrieving_invalid_field_history(self):
        """ test retrieving forbidden field name """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length='7:00'
            )

        res = self.client.get(user_health_statistic_sumamry('user'))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieving_non_existing_field(self):
        """ test retrieving non existing field """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length='7:00'
            )

        res = self.client.get(user_health_statistic_sumamry('nonexisting'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_url_for_strava_auth_initialization(self):
        """ test getting link to strava site if no strava information
        associated with user """

        url = 'https://www.strava.com/oauth/authorize?client_id=69302&response_type=code&redirect_uri=http://localhost:8000/strava-auth&approval_prompt=force&scope=activity:read_all&'
        res = self.client.get(HEALTH_DIARY)
        self.assertIn(url, res.data['_links']['connect-strava'], url)

    @patch('users.selectors.get_activities_from_strava')
    @patch('users.selectors.process_request')
    def test_retrieve_burned_calories_and_calories_delta(self, mock, mock2):
        """ test retreving calories burned, eaten and delta """

        meal = sample_meal(user=self.user)
        today = datetime.date.today()
        start_date_local = f'{today}T06:52:54Z'
        activities = [{
            'id': 1,
            'name': 'test',
            'calories': 1000,
            'start_date_local': start_date_local
        }, ]
        mock2.return_value = activities
        mock.return_value = activities[0]
        res = self.client.get(HEALTH_DIARY)
        data = models.HealthDiary.objects.get(
            date=datetime.date.today(), user=self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(data.calories, meal.calories)
        self.assertEqual(res.data['calories'], data.calories)
        self.assertEqual(res.data['burned_calories'], 1000)
        self.assertEqual(res.data['calories_delta'],
                         data.calories - 1000)
