from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipe.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    """Выполненяем поиск ингредиентов по полю 'name'"""

    search_param = 'name'


class RecipesFilter(FilterSet):
    """Класс фильтра для фильтрации рецептов на основе разных критериев."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shoppingcart_recipe__user=user)
        return queryset
