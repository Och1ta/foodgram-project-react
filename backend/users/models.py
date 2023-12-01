from django.db import models
from django.contrib.auth.models import AbstractUser

from constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                       MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME,
                       MAX_LENGTH_PASSWORD)

from validators import username_regular


class User(AbstractUser):
    """Кастомная модель User"""

    username = models.CharField(
        max_length=MAX_LENGTH_EMAIL,
        blank=False,
        unique=True,
        validators=(username_regular,),
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        blank=False,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_USERNAME,
        blank=False,
        unique=True,
        verbose_name='Электроная почта'
    )
    password = models.CharField(
        max_length=MAX_LENGTH_PASSWORD,
        blank=False,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=('username',), name='unique_username'
            ),
            models.UniqueConstraint(
                fields=('email',), name='unique_email'
            ),
        )

        def __str__(self):
            return self.username


class Follow(models.Model):
    """Кастомная модель для подписок на автора"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик автора'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписался на {self.subscriber}'
