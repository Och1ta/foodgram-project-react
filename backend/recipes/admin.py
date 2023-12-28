from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.constants import ADMIN_INLINE_EXTRA

from recipes.models import (AmountIngredient, Favorite, Ingredient,
                     Recipe, ShoppingCart, Tag)


class IngredientInline(admin.TabularInline):
    model = AmountIngredient
    extra = ADMIN_INLINE_EXTRA


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'pub_date',
        'display_ingredients',
        'display_image',
        'display_favorites_count',
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
    list_filter = ('name', 'author__username', 'tags__name')
    list_display_links = ('name', 'author')
    raw_id_fields = ('author',)
    inlines = (IngredientInline,)
    empty_value_display = '-пусто-'

    @admin.display(description='Ингредиент')
    def display_ingredients(self, obj):
        ingredients_list = [
            ingredient.name for ingredient in obj.ingredients.all()]
        if ingredients_list:
            return ', '.join(ingredients_list)
        return '-'

    @admin.display(description='Изображение')
    def display_image(self, obj):
        return mark_safe(
            f"<img src={obj.image.url} ширина='70' высота='35' граница='3'>")

    @admin.display(description='В избранном')
    def display_favorites_count(self, obj):
        return obj.recipes_favorite_related.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    search_fields = ('name', 'color')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_display_links = ('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_display_links = ('user', 'recipe')
