from rest_framework import serializers
from recipe.models import Ingredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    """ Serializer for ingredient objects """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'slug', 'user', 'type')
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if ingredient with provided name is not already in db """
        user = self.context['request'].user

        """ temporary solution """
        queryset = Ingredient.objects.filter(user=user).filter(name=value)
        if self.instance is None:
            if queryset.exists():
                raise serializers.ValidationError('Składnik o tej nazwie \
                                                    już istnieje!')
        else:
            if queryset.exclude(id=self.instance.id):
                raise serializers.ValidationError('Składnik o tej nazwie \
                                                    już istnieje!')
        """ ------------------ """

        return value


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag objects """

    class Meta:
        model = Tag
        fields = ('id', 'user', 'slug', 'name')
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if tag with provided name is not already in db """

        user = self.context['request'].user

        """ temporary solution """
        queryset = Tag.objects.filter(user=user).filter(name=value)
        if self.instance is None:
            if queryset.exists():
                raise serializers.ValidationError('Tag o tej nazwie \
                                                    już istnieje!')
        else:
            if queryset.exclude(id=self.instance.id):
                raise serializers.ValidationError('Tag o tej nazwie \
                                                    już istnieje!')
        """ ------------------ """


        return value
