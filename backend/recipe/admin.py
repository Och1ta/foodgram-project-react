from django.contrib import admin
from django.contrib.admin import display

from .models import (
    Ingredient, IngredientsAmount, Recipe, ShoppingCart, Tag, Favorite
)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'in_favorites_amount')
    list_filter = ('author', 'name', 'tags')

    @display(description='Кол-во добавлений в избранное.')
    def in_favorites_amount(self, obj):
        """Отображаем общее число добавлений этого рецепта в избранное"""

        return obj.favourites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'units_measurement')
    list_filter = ['name']


class IngredientsAmountAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code', 'slug')
    list_filter = ['slug']


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientsAmount, IngredientsAmountAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
