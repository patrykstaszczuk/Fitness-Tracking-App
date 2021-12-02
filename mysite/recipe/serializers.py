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

    links = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'user',
            'name',
            'slug',
            'calories',
            'links'
        )

    def get_links(self, instance) -> dict:
        """ prepare links to proper endpoints """
        links = []
        if instance.user != self.context['request'].user:
            self_url = reverse('recipe:group-recipe-detail', kwargs={
                'pk': instance.user.id,
                'slug': instance.slug,
            }, request=self.context['request'])
            tags = reverse(
                'recipe:group-recipe-tags',  kwargs={
                    'pk': instance.user.id,
                    'slug': instance.slug
                },
                request=self.context['request'])
        else:
            self_url = reverse('recipe:recipe-detail',
                               kwargs={'slug': instance.slug},
                               request=self.context['request'])
            tags = reverse(
                'recipe:recipe-tags',
                kwargs={'slug': instance.slug},
                request=self.context['request'])
        links.append({
            'self': self_url,
            'tags': tags
        })
        return links

    def to_representation(self, instance) -> dict:
        ret = super().to_representation(instance)

        ret.update({'self': ret['links'][0].get('self')})
        ret.update({'tags': ret['links'][0].get('tags')})
        ret.pop('links')

        return ret


class RecipeDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing recipe object """

    self = serializers.HyperlinkedIdentityField(
        view_name='recipe:recipe-detail', lookup_field='slug')
    tags = serializers.HyperlinkedIdentityField(
        view_name='recipe:recipe-tags', lookup_field='slug')
    ingredients = serializers.HyperlinkedIdentityField(
        view_name='recipe:recipe-ingredients', lookup_field='slug')

    class Meta:
        model = Recipe
        fields = '__all__'


class GroupRecipeDetailOutpuSerializer(RecipeDetailOutputSerializer):

    class GroupRecipeDetailHyperlink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'pk': obj.user.id,
                'slug': obj.slug
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
    self = GroupRecipeDetailHyperlink(view_name='recipe:group-recipe-detail')

    tags = GroupRecipeDetailHyperlink(
        view_name='recipe:group-recipe-tags')
    ingredients = GroupRecipeDetailHyperlink(
        view_name='recipe:group-recipe-ingredients')


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

    class RecipeIngredientUpdateHyperLink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'pk': obj.id,
                'slug': obj.recipe.slug
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    class IngredientHyperLink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'slug': obj.ingredient.slug
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    self = RecipeIngredientUpdateHyperLink(
        view_name='recipe:recipe-ingredients-update')
    ingredient = IngredientHyperLink(view_name='recipe:ingredient-detail')
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=True)
    name = serializers.SerializerMethodField()
    unit = serializers.StringRelatedField()

    class Meta:
        model = Recipe_Ingredient
        fields = ('id', 'name', 'unit', 'amount', 'self', 'ingredient')

    def get_name(self, instance):
        return instance.ingredient.name


class TagOutputSerializer(serializers.ModelSerializer):
    """ serializing Tag output data """

    self = serializers.HyperlinkedIdentityField(
        view_name='recipe:tag-detail', lookup_field='slug')

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name', 'self')


class TagInputSerializer(serializers.Serializer):
    """ serializing Tag input data """

    name = serializers.CharField(max_length=25)


class IngredientListOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredients instances """

    self = serializers.HyperlinkedIdentityField(
        view_name='recipe:ingredient-detail', lookup_field='slug')
    tags = serializers.HyperlinkedIdentityField(
        view_name='recipe:ingredient-tags', lookup_field='slug')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'slug', 'user', 'self', 'tags')


class IngredientDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredient object """

    self = serializers.HyperlinkedIdentityField(
        view_name='recipe:ingredient-detail', lookup_field='slug')
    tags = serializers.HyperlinkedIdentityField(
        view_name='recipe:ingredient-tags', lookup_field='slug')
    units = serializers.HyperlinkedIdentityField(
        view_name='recipe:ingredient-units', lookup_field='slug')

    class Meta:
        model = Ingredient
        fields = '__all__'


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
