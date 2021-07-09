from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from users.models import MyUser
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit
# from users.forms import CustomUserChangeForm, CustomUserCreationForm


class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    # The forms to add and change user instances
    # form = CustomUserChangeForm
    # add_form = CustomUserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'password', 'age', 'sex',
                    'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_superuser',)
    fieldsets = (
        # (Tittle, Fields)
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'age', 'sex')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'fields': ('email', 'name', 'password1', 'password2',
                       'age', 'sex', 'is_staff', 'is_superuser'),
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
