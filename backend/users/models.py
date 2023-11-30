from django.db import models
from django.contrib.auth.models import AbstractUser

from constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                       MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)


class User(AbstractUser):
    """Кастомная модель User"""

    username = models.CharField(
        max_length=MAX_LENGTH_EMAIL,
        blank=False,
        unique=True,
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

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

        def __str__(self):
            return self.username
