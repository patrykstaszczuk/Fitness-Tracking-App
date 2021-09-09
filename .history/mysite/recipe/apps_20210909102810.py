from django.apps import AppConfig


class RecipeConfig(AppConfig):
    name = 'recipe'

    def ready(self):
        import recipe.signals
