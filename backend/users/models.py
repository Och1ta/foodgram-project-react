from django.db import models
from django.contrib.auth.models import AbstractUser

from users.validators import validate_username


class User(AbstractUser):
    """Кастомная модель User"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'first_name',
        'last_name', 'password',
    )

    username = models.CharField(
        max_length=254,
        blank=False,
        unique=True,
        validators=[validate_username],
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=150,
        blank=False,
        unique=True,
        verbose_name='Электроная почта'
    )
    password = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

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
        return f'{self.user} подписался на {self.following}'
