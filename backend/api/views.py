from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, SAFE_METHODS)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipesFilter
from api.paginations import CustomPagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    AddRecipeSerializer, CustomUserSerializer, FavoriteSerializer,
    IngredientSerializer, RecipeSerializer, ShoppingCartSerializer,
    SubscriptionSerializer, TagSerializer
)
from api.utils import download_shopping_cart
from recipe.models import (
    Ingredient, IngredientInRecipe, Recipe, Tag,
    ShoppingCart, Favorite
)
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    """Кастомный юзер с определенным набором полей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        url_name='me',
        permission_classes=(IsAuthenticated, )
    )
    def get_me(self, request):
        """Информация о себе"""
        if request.method == 'PATCH':
            serializer = CustomUserSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        serializer = SubscriptionSerializer(
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

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            author__user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request})
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

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients')
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return AddRecipeSerializer

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

        if not model_obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """
        Добавить рецепт в список избранное.
        Доступно только авторизованным пользователям.
        """
        serializer = FavoriteSerializer(
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
            {'error': 'Такого рецепта нет!'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавить рецепт в список покупок.
        Доступно только авторизованным пользователям.
        """
        serializer = ShoppingCartSerializer(
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
            {'error': 'Такого рецепта нет!'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
        pagination_class=None
    )
    def download_shopping_cart_txt(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart_recipe__user=request.user).order_by(
                'ingredient__name').values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        return download_shopping_cart(ingredients)
