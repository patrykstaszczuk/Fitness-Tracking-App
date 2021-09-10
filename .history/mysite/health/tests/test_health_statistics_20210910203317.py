from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from health import models

from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from users import serializers as user_serializers
from users import models as user_models
from health import serializers as health_serializers
from health.models import HealthDiary
from recipe.models import Recipe, Ingredient, Unit
from meals_tracker.models import Meal, MealCategory

from unittest.mock import patch, MagicMock
import datetime
import time

USER_DAILY_HEALTH_DASHBOARD = reverse('health:health-diary')
USER_HEALTH_STATISTIC_RAPORT = reverse('health:health-list')
USER_HEALTH_STATISTIC_WEEKLY_SUMMARY = reverse('health:weekly-summary')

NOW = datetime.date.today()


def user_health_specific_stat_raport(slug):
    return reverse('health:health-detail', kwargs={'slug': slug})


def user_healh_statistic_raport_detail(slug):
    """ reverse for user health statistic detail """
    return reverse('health:health-detail', kwargs={'slug': slug})


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


def sample_meal(user):
    """ create and return meal object """
    recipe = Recipe.objects.create(user=user, name='test', portions=4)
    unit = Unit.objects.create(name='gram')
    category = MealCategory.objects.create(name='breakfast')
    ingredient = Ingredient.objects.create(user=user, name='ing',
                                           calories=1000)
    recipe.ingredients.add(ingredient, through_defaults={"unit": unit,
                                                         "amount": 100})
    meal = Meal.objects.create(user=user, category=category)
    meal.recipes.add(recipe, through_defaults={"portion": 1})
    return meal

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
            gender='Male'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.request = APIRequestFactory().get('/')

    def test_retrieve_user_information(self):
        """ test retrieving information about user """

        url = reverse('users:profile')
        res = self.client.get(url)
        serializer = user_serializers.UserSerializer(self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_calculate_user_bmi(self):
        """ test calculating BMI based on user height and weight """

        url = reverse('health:bmi')

        res = self.client.get(url)
        bmi = self.user.get_bmi()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['bmi'], bmi)

    def test_retrieve_user_daily_health_statistics(self):
        """ test retrieving requested user daily health statistics """

        daily_data = models.HealthDiary.objects.create(
            user=self.user,
            calories=1000,
            weight=70,
            sleep_length='07:14:00'
        )

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        serializer = health_serializers.HealthDiaryOutputSerializer(daily_data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_proper_calories_amount_based_on_meals(self):
        """ test auto calculation calories for daily healt statistic
        based on meals from given day """

        user2 = sample_user()
        category = MealCategory.objects.create(name='breakfast')
        recipe = Recipe.objects.create(user=self.user, name='test', calories=1000, portions=4)
        meal1 = Meal.objects.create(user=self.user, category=category)
        meal1.recipes.add(recipe, through_defaults={"recipe": recipe, "portion": 1})
        meal2 = Meal.objects.create(user=self.user, category=category)
        ingredient = Ingredient.objects.create(user=user2, name='skladnik', calories=500)
        unit = Unit.objects.get(name='gram')
        meal2.ingredients.add(ingredient, through_defaults={"amount": 100, "unit": unit})
        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['calories'], recipe.calories/4 + ingredient.calories)

    def test_retrieve_daily_health_statistics_limited_to_user(self):
        """ test retrieving statistics belongs to request user only """
        user2 = sample_user()
        models.HealthDiary.objects.create(user=user2, weight=63)
        data = models.HealthDiary.objects.create(user=self.user, weight=75)

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        serializer = health_serializers.HealthDiaryOutputSerializer(data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_health_diary_just_for_today(self):
        """ test retrieving only daily info """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74.2)

        models.HealthDiary.objects.create(user=self.user, date='2021-05-27',
                                          weight=73.2)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-26',
                                          weight=73.9)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-25',
                                          weight=72.3)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-24',
                                          weight=71.9)

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)

        serializer = health_serializers.HealthDiarySerializer(diary)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_user_daily_health_statistics(self):
        """ test adding basic statistics """

        payload = {
            'weight': 74.3,
            'sleep_length': '7:24:00',
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.patch(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        daily_data = models.HealthDiary.objects.filter(user=self.user). \
            get(date=datetime.date.today())
        serializer = health_serializers.HealthDiaryInputSerializer(daily_data)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_update_user_daily_health_statistics_with_patch(self):
        """ test updating user diary with patch request """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74.5)

        payload = {
            'sleep_length': '8:00:0',
            'weight': '75.5',
        }

        res = self.client.patch(USER_DAILY_HEALTH_DASHBOARD, payload,
                                format='json')
        diary.refresh_from_db()
        serializer = health_serializers.HealthDiaryOutputSerializer(diary)
        
        self.assertEqual(res.json(), serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_creating_user_daily_health_statistics_with_invalid_values(self):
        """ test updating failed due to invalid values """

        payload = {
            'sleep_length': '1000',
            'weight': '1000',
            'rest_heart_rate': '1000',
            'calories': '2000',
        }

        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_updating_user_diary_forbidden_fields_failed(self):
        """ test updating user and date failed """

        payload = {
            'user': 'user2',
            'date': '2020-03-30'
        }

        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        self.assertNotEqual(res.json()['data']['date'], payload['date'])

    def test_updating_user_weight_with_null(self):
        """ test setting weight to blank value """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74)

        payload = {
            'weight': None,
            'sleep_length': '7',
            'daily_thoughts': ''
            }
        res = self.client.put(USER_DAILY_HEALTH_DASHBOARD, payload,
                              format='json')
        diary.refresh_from_db()
        serializer = health_serializers.HealthDiarySerializer(diary)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_health_statistics_raport(self):
        """ test retrieving health statistics history list"""

        diaries_list = []
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                            date='2021-05-27', weight=73.2))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                            date='2021-05-26', weight=73.2))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                            date='2021-05-25', weight=73.2))
        diaries_list.append(models.HealthDiary.objects.create(user=self.user,
                            date='2021-05-24', weight=73.2))

        res = self.client.get(USER_HEALTH_STATISTIC_RAPORT)
        serializer = health_serializers.HealthRaportSerializer(diaries_list,
                                                               many=True,
                                                               context={'request': self.request})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_health_statistics_raport_users_separation(self):
        """ test users separation during retrieving health history """

        user2 = sample_user()
        diaries = []
        user2_diary = models.HealthDiary.objects.create(user=user2,
                                                        date='2021-05-22')
        diaries.append(models.HealthDiary.objects.create(user=self.user,
                                                         date='2021-05-22'))
        diaries.append(models.HealthDiary.objects.create(user=self.user,
                                                         date='2021-05-23'))

        res = self.client.get(USER_HEALTH_STATISTIC_RAPORT)

        u2_serializer = health_serializers.HealthRaportSerializer(user2_diary,
                                                                  context={'request': self.request})
        serializer = health_serializers.HealthRaportSerializer(diaries,
                                                               many=True,
                                                               context={'request': self.request})
        self.assertNotIn(u2_serializer, res.data)
        self.assertEqual(res.data, serializer.data)

    def test_exclude_today_statistics_from_history(self):
        """ test excluding today's statistic from history """

        history = []
        history.append(models.HealthDiary.objects.create(user=self.user,
                                                         date='2021-05-25'))
        history.append(models.HealthDiary.objects.create(user=self.user,
                                                         date='2021-05-26'))
        today = models.HealthDiary.objects.create(user=self.user)
        res = self.client.get(USER_HEALTH_STATISTIC_RAPORT)

        serializer = health_serializers.HealthRaportSerializer(today,
                                        context={'request': self.request})
        self.assertNotIn(serializer.data, res.data)

    def test_post_not_allowed_on_health_history_site(self):
        """ test method POST not allowed on health history site """

        res = self.client.post(USER_HEALTH_STATISTIC_RAPORT, {'data': 'data'})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieving_health_statistic_detail(self):
        """ test retrieving health statistic history detail """
        test = models.HealthDiary.objects.create(user=self.user, date=datetime.date(2021, 3, 22))
        models.HealthDiary.objects.create(user=self.user)
        diary = models.HealthDiary.objects.create(user=self.user,
                                                  date=datetime.date(2021, 5, 22), weight=65)

        res = self.client.get(user_healh_statistic_raport_detail(diary.slug))
        serializer = health_serializers.HealthDiarySerializer(diary)

        self.assertEqual(res.data, serializer.data)

    def test_retrieving_health_statistic_detail_users_separation(self):
        """ test users separation when retrieving health statistics detail """

        user2 = sample_user()

        models.HealthDiary.objects.create(user=user2, date='2021-05-30')
        diary = models.HealthDiary.objects.create(user=self.user,
                                                  date='2021-05-30')

        res = self.client.get(user_healh_statistic_raport_detail(diary.slug))

        serializer = health_serializers.HealthDiarySerializer(diary)
        self.assertEqual(res.data, serializer.data)

    def test_delete_health_statistic_not_allowed(self):
        """ test method DELETE not allowed in healt statistic detail """

        diary = models.HealthDiary.objects.create(user=self.user)

        res = self.client.delete(user_healh_statistic_raport_detail(
            diary.slug))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_history_statistic_success(self):
        """ test updating history statistics """

        diary = models.HealthDiary.objects.create(user=self.user,
                                                  calories=1000,
                                                  date='2021-05-12')
        payload = {
            'weight': '74',
            'rest_heart_rate': None,
            'sleep_length': '5'
        }
        res = self.client.put(user_healh_statistic_raport_detail(diary.slug),
                              payload, format='json')
        diary.refresh_from_db()
        serializer = health_serializers.HealthDiarySerializer(diary)

        self.assertEqual(res.data, serializer.data)

    def test_updating_other_user_statistics_failed(self):
        """ test user separation feature """

        user2 = sample_user()

        user2_diary = models.HealthDiary.objects.create(user=user2,
                                                        date='2021-05-20')

        res = self.client.put(user_healh_statistic_raport_detail(
                user2_diary.slug))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieving_weekly_average_health_stats_for_user(self):
        """ test retrieving average stats for user """

        avg_weight = 0
        for i in range(1, 8):
            diary = models.HealthDiary.objects.create(
                user=self.user,
                weight=70+i,
                date=datetime.date.today() - datetime.timedelta(days=i)
            )
            avg_weight += diary.weight
        avg_weight = avg_weight/7

        res = self.client.get(USER_HEALTH_STATISTIC_WEEKLY_SUMMARY)
        self.assertEqual(res.data['weight'], avg_weight)

    def test_retrieving_weigth_history(self):
        """ test getting all weight entries """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                weight=70+i
            )
        res = self.client.get(user_health_specific_stat_raport('weigth'),
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

    def test_retrieving_sleep_length_history(self):
        """ test retrieving all sleep length entries """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length=7
            )

        res = self.client.get(user_health_specific_stat_raport('sleep_length'),
                              format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

    def test_retrieving_invalid_field_history(self):
        """ test retrieving forbidden field name """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length=7
            )

        res = self.client.get(user_health_specific_stat_raport('user'))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_post_not_allowed_in_stat_history(self):
        """ test post request failed """

        res = self.client.post(user_health_specific_stat_raport('waga'))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieving_non_existing_field(self):
        """ test retrieving non existing field """

        for i in range(1, 6):
            models.HealthDiary.objects.create(
                user=self.user,
                date=f'2021-05-{i}',
                sleep_length=7
            )

        res = self.client.get(user_health_specific_stat_raport('nonexisting'))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieving_no_content(self):
        """ test retrieving 204 status if no content is returned """

        res = self.client.get(user_health_specific_stat_raport('weight'))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieving_statistic_by_non_authenticated_user_failed(self):
        """ test authentication feature """

        self.user2 = APIClient()

        res = self.user2.get(user_health_specific_stat_raport('weight'))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_url_for_strava_auth_initialization(self):
        """ test getting link to strava site if no strava information
        associated with user """

        url = 'https://www.strava.com/oauth/authorize?client_id=69302&response_type=code&redirect_uri=http://localhost:8000/strava-auth&approval_prompt=force&scope=activity:read_all&'
        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        self.assertIn(url, res.json()['_links']['connect-strava'], url)

    @patch('users.models.StravaApi.get_strava_activities')
    @patch('users.models.StravaApi._process_request')
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
        },]
        mock2.return_value = activities
        mock.return_value = activities[0]
        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        data = HealthDiary.objects.get(date=datetime.date.today(), user=self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(data.calories, meal.calories)
        self.assertEqual(res.json()['data']['calories'], data.calories)
        self.assertEqual(res.json()['data']['burned_calories'], 1000)
        self.assertEqual(res.json()['data']['calories_delta'],
                         data.calories - 1000)
