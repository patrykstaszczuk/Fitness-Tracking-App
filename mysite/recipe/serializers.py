from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit, \
    Ingredient_Unit
from rest_framework.reverse import reverse


class RecipeInputSerializer(serializers.Serializer):

    name = serializers.CharField(required=False)
    portions = serializers.IntegerField(required=False)
    prepare_time = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False)


class RecipeListOutputSerializer(serializers.ModelSerializer):
    """ serializing list of recipe objects """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Recipe
        fields = (
            'id',
            'user',
            'name',
            'slug',
            'calories',
            '_links'
        )

    def get_links(self, instance) -> dict:
        """ prepare links to proepr endpoints """
        links = []
        if instance.user != self.context['request'].user:
            self_url = reverse('recipe:group-recipe-detail', kwargs={
                'pk': instance.user.id,
                'slug': instance.slug,
            })
        else:
            self_url = reverse('recipe:recipe-detail',
                               kwargs={'slug': instance.slug})

        links.append({
            'rel': 'self',
            'href': self_url,

        })
        links.append({
            'rel': 'tags',
            'href': reverse('recipe:recipe-tags',  kwargs={'slug': instance.slug}),

        })
        return links


class RecipeDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing recipe object """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Recipe
        exclude = ('tags', 'ingredients')

    def get_links(self, instance) -> list:
        """ prepare links to proepr endpoints """
        links = []
        self_rel = {
            'rel': 'self',
            'href': reverse('recipe:recipe-detail', kwargs={'slug': instance.slug}),
        }

        links.append(self_rel)

        tags = {
            'rel': 'tags',
            'href': reverse('recipe:recipe-tags',  kwargs={'slug': instance.slug}),
        }
        links.append(tags)

        ingredients = {
            'rel': 'ingredients',
            'href': reverse('recipe:recipe-ingredients',  kwargs={'slug': instance.slug}),
        }
        links.append(ingredients)
        return links


class GroupRecipeDetailOutpuSerializer(RecipeDetailOutputSerializer):

    def get_links(self, instance) -> list:
        links = []
        self_rel = {
            'rel': 'self',
            'href': reverse('recipe:group-recipe-detail',
                            kwargs={
                                'pk': instance.user.id,
                                'slug': instance.slug
                                }),
        }

        links.append(self_rel)

        tags = {
            'rel': 'tags',
            'href': reverse('recipe:group-recipe-tags',
                            kwargs={
                                'pk': instance.user.id,
                                'slug': instance.slug}),
        }
        links.append(tags)

        ingredients = {
            'rel': 'ingredients',
            'href': reverse('recipe:group-recipe-ingredients',
                            kwargs={
                                'pk': instance.user.id,
                                'slug': instance.slug}),
        }
        links.append(ingredients)
        return links


class TagsIdsSerializer(serializers.Serializer):
    """ serializer for managing tags related to recipe """

    tag_ids = serializers.ListField(child=serializers.IntegerField())


class RecipeIngredientsHelperSerializer(serializers.Serializer):
    """ helper serializer for recipe ingredient """
    ingredient = serializers.IntegerField()
    amount = serializers.IntegerField()
    unit = serializers.IntegerField()


class RecipeIngredientsInputSerializer(serializers.Serializer):
    """ serializer for adding ingredients with amount and unit to recipe """

    ingredients = RecipeIngredientsHelperSerializer(many=True)


class RecipeIngredientUpdateSerializer(serializers.Serializer):
    """ serializer for updating recipe ingredients """
    amount = serializers.IntegerField()
    unit = serializers.IntegerField()


class RecipeIngredientsRemoveSerializer(serializers.Serializer):
    """ serializer for removing ingredients from recipe """

    ingredient_ids = serializers.ListField(child=serializers.IntegerField())


class RecipeIngredientOutputSerializer(serializers.ModelSerializer):
    """ serializer for Recipe Ingredient intermediate model """

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=True)
    ingredient = serializers.StringRelatedField()
    unit = serializers.StringRelatedField()
    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Recipe_Ingredient
        fields = ('id', 'ingredient', 'unit', 'amount', '_links')

    def get_links(self, instance):
        links = []
        self_link = {
            'rel': 'self',
            'href': reverse('recipe:recipe-ingredients-update',
                            kwargs={
                                'slug': instance.recipe.slug,
                                'pk': instance.ingredient.id})
        }
        ingredient_link = {
            'rel': 'ingredient',
            'href': reverse('recipe:ingredient-detail',
                            kwargs={'slug': instance.ingredient.slug})
        }
        links.append(self_link)
        links.append(ingredient_link)
        return links


class TagOutputSerializer(serializers.ModelSerializer):
    """ serializing Tag output data """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name', '_links')

    def get_links(self, instance):
        links = []
        self_link = {
            'rel': 'self',
            'href': reverse('recipe:tag-detail', kwargs={'slug': instance.slug})
        }

        links.append(self_link)
        return links


class TagInputSerializer(serializers.Serializer):
    """ serializing Tag input data """

    name = serializers.CharField(max_length=25)


class IngredientListOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredients instances """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'slug', 'user', '_links')

    def get_links(self, instance) -> list:
        links = []
        self_rel = {
            'rel': 'self',
            'href': reverse('recipe:ingredient-detail', kwargs={'slug': instance.slug})
        }
        tags = {
            'rel': 'tags',
            'href': reverse('recipe:ingredient-tags', kwargs={'slug': instance.slug})
        }
        links.append(self_rel)
        links.append(tags)
        return links


class IngredientDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredient object """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Ingredient
        exclude = ('units', 'tags')

    def get_links(self, instance) -> list:
        links = []
        self_rel = {
            'rel': 'self',
            'href': reverse('recipe:ingredient-detail', kwargs={'slug': instance.slug})
        }
        tags = {
            'rel': 'tag',
            'href': reverse('recipe:ingredient-tags', kwargs={'slug': instance.slug})
        }
        units = {
            'rel': 'unit',
            'href': reverse('recipe:ingredient-units', kwargs={'slug': instance.slug})
        }
        links.append(self_rel)
        links.append(tags)
        links.append(units)
        return links


class IngredientInputSerializer(serializers.Serializer):
    """ serializing Ingredient input data """

    ready_meal = serializers.BooleanField(required=False)
    name = serializers.CharField(max_length=255, required=False)
    calories = serializers.FloatField(min_value=0, required=False)
    proteins = serializers.FloatField(min_value=0, required=False)
    carbohydrates = serializers.FloatField(min_value=0, required=False)
    fats = serializers.FloatField(min_value=0, required=False)
    choices = [
        ('S', 'solid'),
        ('L', 'liquid')
    ]

    type = serializers.ChoiceField(choices, required=False)
    fiber = serializers.FloatField(min_value=0, required=False)
    sodium = serializers.FloatField(min_value=0, required=False)
    potassium = serializers.FloatField(min_value=0, required=False)
    calcium = serializers.FloatField(min_value=0, required=False)
    iron = serializers.FloatField(min_value=0, required=False)
    magnesium = serializers.FloatField(min_value=0, required=False)
    selenium = serializers.FloatField(min_value=0, required=False)
    zinc = serializers.FloatField(min_value=0, required=False)


class IngredientUnitSerializer(serializers.Serializer):
    """ serializer for mapping unit to ingredients """
    unit = serializers.IntegerField()
    grams = serializers.IntegerField()


class UnitOutputSerializer(serializers.ModelSerializer):
    """ serializing available units """

    class Meta:
        model = Unit
        fields = '__all__'
