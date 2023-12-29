from django.contrib import admin

from recipes.constants import ADMIN_INLINE_EXTRA
from recipes.models import (
    AmountIngredient, Favorite, Ingredient,
    Recipe, ShoppingCart, Tag
)


class IngredientInRecipeInline(admin.TabularInline):
    model = AmountIngredient
    extra = ADMIN_INLINE_EXTRA


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'author',
        'count_favorite'
    )
    fields = (
        ('name', 'tags',),
        ('text', 'cooking_time'),
        ('author', 'image'),
    )
    search_fields = (
        'name',
        'author__username',
        'tags__name',
    )
    list_filter = ('author', 'name', 'tags')
    inlines = [IngredientInRecipeInline]
    empty_value_display = '-пусто-'

    def count_favorite(self, obj):
        return obj.recipes_favorite_related.count()


@admin.register(AmountIngredient)
class AmountIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)
