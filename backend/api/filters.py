from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Выполненяем поиск ингредиентов по полю 'name'."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Класс фильтра для фильтрации рецептов на основе разных критериев."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                recipes_favorite_related__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                recipes_shoppingcart_related__user=self.request.user)
        return queryset
