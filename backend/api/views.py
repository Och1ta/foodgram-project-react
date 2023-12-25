from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipesFilter
from api.paginations import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AddRecipeSerializer, CustomUserSerializer, FavoriteSerializer,
    IngredientSerializer, RecipeSerializer, ShoppingCartSerializer,
    SubscriptionSerializer, TagSerializer
)
from recipe.models import Ingredient, IngredientInRecipe, Recipe, Tag
from rest_framework.views import APIView
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    """Кастомный юзер с определенным набором полей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=(IsAuthenticated,)
    )
    def post(self, request):
        user_id = self.kwargs.get('user_id')
        if Subscription.objects.filter(
            user=request.user,
            author_id=user_id
        ).exists():
            return Response(
                {'Вы уже подписаны на автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, id=user_id)
        Subscription.objects.create(
            user=request.user,
            author_id=user_id
        )
        return Response(
            self.serializer_class(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def delete(self, request):
        user_id = self.kwargs.get('user_id')
        get_object_or_404(User, id=user_id)
        subscription = Subscription.objects.filter(
            user=request.user,
            author_id=user_id
        )
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'Вы не подписаны на пользователя'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Возвращает список пользователей,
        на которых подписан текущий пользователь.
        """
        subscriptions = User.objects.filter(
            author__user=request.user
        )
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return AddRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def recipe_post_delete(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        model_obj = serializer_class.Meta.model.objects.filter(
            user=user, recipe=recipe
        )

        if self.request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': pk},
                context={'request': self.request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        else:
            if not model_obj.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
        model_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, pk=None):
        """
        Добавить рецепт в список избранное.
        Доступно только авторизованным пользователям.
        """
        return self.recipe_post_delete(pk, FavoriteSerializer)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, pk=None):
        """
        Добавить рецепт в список покупок.
        Доступно только авторизованным пользователям.
        """
        return self.recipe_post_delete(pk, ShoppingCartSerializer)


class DownloadShoppingCartViewSet(APIView):
    """Метод загрузки списка покупки"""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart_recipe__user=request.user).order_by(
            'ingredient__name').values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(
                f'\n{name} - {amount}, {measurement_unit}'
            )
        filename = 'shopping_list.txt'
        response = HttpResponse(
            shopping_list, content_type='text/plain'
        )
        response['Content-Disposition'] = \
            f'attachment; filename={filename}'
        return response
