from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from backend.api.serializers import UserSerializer, FollowingSerializer, IngredientSerializer, TagSerializer, \
    GetRecipeSerializer, PostRecipeSerializer, ShortRecipeCellSerializer
from backend.recipe.filters import SearchIngredientFilter, RecipeFilter
from backend.recipe.models import Ingredient, Tag, Recipe, Favorite, ShoppingCart, IngredientsAmount
from backend.recipe.permissions import IsUserOrAdmin
from backend.users.models import Follow


User = get_user_model()


class UserViewSet(UserViewSet):
    """Кастомный юзер с определенным набором полей."""

    queryset = User.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = UserSerializer

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """
        Запрещаем неавторизованному пользователю доступ
        к странице текущего пользователя.
        """
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        """Подписаться на пользователя."""
        user = request.user
        author = get_object_or_404(User, id=kwargs['id'])
        if request.method == 'POST':
            serializer = FollowingSerializer(
                author, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                subscription = Follow.objects.get(
                    user=user,
                    following=author
                )
            except Follow.DoesNotExist:
                return Response(
                    {'errors': 'Подписка не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Возвращает список пользователей,
        на которых подписан текущий пользователь.
        """
        user_following_ids_set = set(
            Follow
            .objects
            .filter(user=request.user)
            .values_list('following', flat=True)
        )
        queryset = self.paginate_queryset(
            User.objects.filter(pk__in=user_following_ids_set)
        )
        serializer = FollowingSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SearchIngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Получаем список рецептов и конкретный рецепт."""

    pagination_class = PageNumberPagination
    permission_classes = (IsUserOrAdmin,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all().order_by('-id')
        return queryset

    def perform_create(self, serializer):
        """Определяем текущего пользователя."""
        if not self.request.user.is_authenticated:
            raise PermissionDenied(
                'Только авторизованный пользователь может создать рецепт.'
            )
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Проверка на создание рецепта только авторизованному пользователю."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Only registered users can create recipes.'},
                status=401)
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от типа запроса."""
        if self.action in SAFE_METHODS:
            return GetRecipeSerializer
        return PostRecipeSerializer

    def add_or_remove(self, request, model, recipe, message):
        """
        Функция создания/удаления для
        списка избранного и списка покупок.
        """
        if request.method == 'POST':
            serializer = ShortRecipeCellSerializer(
                recipe,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            if recipe is None:
                return Response(
                    {'errors': 'Рецепт не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                model.objects.create(user=request.user, recipe=recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response({'errors': 'Уже в списке.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if not model.objects.filter(user=request.user,
                                        recipe=recipe).exists():
                return Response({'errors': 'Рецепт не существует.'},
                                status=status.HTTP_400_BAD_REQUEST)

            get_object_or_404(model, user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': message},
                            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавить рецепт в список избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_or_remove(
            request,
            Favorite,
            recipe,
            'Рецепт удален из избранного.'
        )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавить рецепт в список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_or_remove(
            request,
            ShoppingCart,
            recipe,
            'Рецепт удален из списка покупок.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        recipes_for_shopping_lists = Recipe.objects.filter(
            shoppinglist__user=request.user
        )
        ingredients = IngredientsAmount.objects.filter(
            recipe__in=recipes_for_shopping_lists
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient__amount']
            shopping_list.append(f'\n{name} - {amount} {measurement_unit}')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_list.txt"')
        return response
