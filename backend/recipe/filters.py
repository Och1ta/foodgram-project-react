from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class SearchIngredientFilter(FilterSet):
    """
    Выполненяем поиск ингредиентов по полю 'name'
    в регистронезависимом режиме и по вхождению в начало названия.
    """

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Класс фильтра для фильтрации рецептов на основе разных критериев."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        help_text='Фильтровать рецепты по тегам.'
    )

    is_favorited = filters.NumberFilter(
        method='filter_is_favorited',
        help_text='Фильтровать рецепты, добавленные в избранное.',
    )

    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart',
        help_text='Фильтровать рецепты, находящиеся в корзине покупок.',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filter_is_favorited(self, queryset, value: int):
        """Фильтрует рецепты, добавленные пользователем в избранное."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favourites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, value):
        """Фильтрует рецепты, находящиеся в корзине покупок пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shop_recipe__user=self.request.user)
        return queryset
