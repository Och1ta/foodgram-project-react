from django.contrib import admin

from .models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe,
    ShoppingCart, Tag
)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'count_favorite')
    search_fields = ('author', 'name', 'tags')
    list_filter = ('author', 'name', 'tags')
    inlines = [IngredientInRecipeInline]
    empty_value_display = '-пусто-'

    def count_favorite(self, obj):
        """Отображаем общее число добавлений этого рецепта в избранное"""
        return obj.favorite_recipe.count()

    def display_ingredients(self, obj):
        ingredients_list = [
            ingredient.name for ingredient in obj.ingredients.all()
        ]
        if ingredients_list:
            return ', '.join(ingredients_list)
        return '-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)
