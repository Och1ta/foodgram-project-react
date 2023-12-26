from django.contrib.auth import get_user_model
from django.db.models import Sum, OuterRef, Exists, Value, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated
)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipesFilter
from api.paginations import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    SubscribeSerializer, TagSerializer, IngredientSerializer,
    RecipeSerializer,AddRecipeSerializer, FavoriteSerializer,
    ShoppingCartSerializer
)
from api.utils import download_shopping_cart
from recipe.models import (
    Ingredient, IngredientInRecipe, Recipe, Tag, Favorite, ShoppingCart
)
from users.models import Subscription


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet для управление пользователями."""
    http_method_names = ('get', 'head', 'options', 'post', 'delete')

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return super().get_queryset()
        return super().get_queryset().annotate(
            is_subscribed=Exists(Subscription.objects.filter(
                user=self.request.user,
                author=OuterRef('pk')
            ))
        )

    @action(
        ('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        """Просмотр своей учетной записи."""
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    def get_subscriptions(self):
        return (
            Subscription.objects
            .filter(user=self.request.user)
            .annotate(
                is_subscribed=Value(True),
                recipes_count=Count('author__recipes')
            )
            .select_related('author')
            .prefetch_related('author__recipes')
            .order_by('-pk')
        )

    @action(
        ('get',), detail=False,
        serializer_class=SubscribeSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, *args, **kwargs):
        """Просмотр подписок пользователя."""
        self.get_queryset = self.get_subscriptions
        return self.list(request, *args, **kwargs)

    @action(
        ('post',),
        detail=True,
        serializer_class=SubscribeSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Создание подписки."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        author = get_object_or_404(User, id=id)
        serializer.save(user=request.user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Удаление подписки."""
        subscribtion = get_object_or_404(
            Subscription, user=request.user, author=id
        )
        subscribtion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        if not model_obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST'],
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
        methods=['POST'],
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
