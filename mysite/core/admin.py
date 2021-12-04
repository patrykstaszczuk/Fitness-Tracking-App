from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from users.models import MyUser
from users.models import Group as CustomGroup
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit, \
                          Ingredient_Unit
from meals_tracker.models import Meal, MealCategory


class UserAdmin(BaseUserAdmin):
    ordering = ('email',)

    list_display = ('email', 'password', 'age', 'gender',
                    'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_superuser',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'age', 'gender')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'name', 'password1', 'password2',
                       'age', 'gender', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('email',)

    filter_horizontal = ()


admin.site.register(MyUser, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(Recipe_Ingredient)
admin.site.register(Unit)
admin.site.register(CustomGroup)
admin.site.register(Ingredient_Unit)
admin.site.register(Meal)
admin.site.register(MealCategory)
