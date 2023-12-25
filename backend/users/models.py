from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F

from users.constants import (
    MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME, MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME, MAX_LENGTH_PASSWORD
)
from users.validators import username_validator


class User(AbstractUser):
    """Кастомная модель User"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'first_name',
        'last_name', 'password',
    )

    email = models.EmailField(
        'Электронная почта',
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=MAX_LENGTH_USERNAME,
        validators=(username_validator,),
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_FIRST_NAME,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
    )
    password = models.CharField(
        'Пароль',
        max_length=MAX_LENGTH_PASSWORD,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Кастомная модель для подписок на автора"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='user_not_author',
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.author}'
