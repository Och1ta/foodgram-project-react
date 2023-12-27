from io import StringIO

from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import CustomPagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    FavoriteCreateDeleteSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeReadSerializer,
    ShoppingCartCreateDeleteSerializer, SubscribeCreateSerializer,
    SubscribeSerializer, TagSerializer
)
from recipes.models import (AmountIngredient, Favorite, Ingredient,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription, User


class UserViewSet(UserViewSet):
    """ViewSet модели User"""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=['post'], detail=True,
        permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        serializer = SubscribeCreateSerializer(
            data={'user': request.user.id, 'author': id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        subscription = Subscription.objects.filter(
            user=request.user, author=id)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'no such subscribe'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            author__user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscribeSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet модели Recipe."""

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients')
    permission_classes = [AuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        methods=['post'], detail=True,
        permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить рецепт в список избранное."""
        serializer = FavoriteCreateDeleteSerializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из списка избранного"""
        instance = Favorite.objects.filter(
            user=request.user, recipe_id=pk)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'no such recipe'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post'], detail=True,
        permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок."""
        serializer = ShoppingCartCreateDeleteSerializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок"""
        instance = ShoppingCart.objects.filter(
            user=request.user, recipe_id=pk)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'no such recipe'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        text_stream = StringIO()
        text_stream.write('Список покупок\n')
        text_stream.write('Ингредиент - Единица измерения - Количество\n')
        shopping_cart = (
            AmountIngredient.objects.select_related('recipe', 'ingredient')
            .filter(recipe__recipes_shoppingcart_related__user=request.user)
            .values_list(
                'ingredient__name',
                'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name'))
        lines = (' - '.join(map(str, item)) + '\n' for item in shopping_cart)
        text_stream.writelines(lines)
        response = HttpResponse(
            text_stream.getvalue(),
            content_type='text/plain')
        response['Content-Disposition'] = (
            "attachment;filename='shopping_cart.txt'")
        return response
