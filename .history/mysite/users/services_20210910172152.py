from users.selectors import get_strava_last_request_epoc_time, get_activities_from_strava, prepare_strava_request_url, prepare_authorization_header, process_request, get_activity_properties
import datetime
from django.contrib.auth import get_user_model
from users.models import StravaActivity


def update_activities(user: get_user_model, date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""

    hour = 1
    raw_strava_activities = []
    if get_strava_last_request_epoc_time(user=user) > -1:
        raw_strava_activities = get_activities_from_strava(user=user, date=date)
        process_and_save_strava_activities(user, raw_strava_activities)

def process_and_save_strava_activities(user: get_user_model, raw_strava_activities: list) -> None:
    """ convert raw activities into StravaActivity objects
    """
    if raw_strava_activities and isinstance(raw_strava_activities, list):
        activity_objects = []
        for activity in raw_strava_activities:
            strava_id = activity.get('id', None)
            if not strava_id:
                continue
            url = prepare_strava_request_url(id=strava_id)
            header = prepare_authorization_header(strava_obj=user.strava)
            strava_activity = process_request(url, header, 'GET')
            if strava_activity:
                defaults = get_activity_properties(strava_activity)
                obj, created = StravaActivity.objects.update_or_create(
                    strava_id=strava_id, user=user, **defaults)
                activity_objects.append(obj)
        return activity_objects
    return None