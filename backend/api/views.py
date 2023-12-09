from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from backend.api.serializers import UserSerializer, FollowingSerializer
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
