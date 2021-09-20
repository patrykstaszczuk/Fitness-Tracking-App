from django.apps import AppConfig


class MealsTrackerConfig(AppConfig):
    name = 'meals_tracker'

    def ready(self):
        import meals_tracker.signals
