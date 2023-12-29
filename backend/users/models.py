from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models

from recipes.constants import (MAX_LEN_EMAIL, MAX_LEN_NAME,)
from users.validators import username_validator


class User(AbstractUser):
    """Кастомная модель User."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'first_name',
        'last_name', 'password',
    )

    email = models.EmailField(
        'Электронная почта',
        max_length=MAX_LEN_EMAIL,
        unique=True,
        validators=[EmailValidator],
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LEN_NAME,
        unique=True,
        validators=(username_validator,),
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LEN_NAME,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LEN_NAME,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return '{} {}'.format(self.username, self.email)


class Subscription(models.Model):
    """Кастомная модель для подписок на автора."""

    user = models.ForeignKey(
        User,
        related_name='followed_users',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name=(
                    '\n%(app_label)s_%(class)s пользователь не может '
                    'дважды подписаться на одного и того же автора\n'),
            ),
        )

    def __str__(self):
        return '{} {}'.format(self.user, self.author)

    def save(self, *args, **kwargs):
        if self.user == self.author:
            raise ValidationError('Вы не можете подписаться на себя')
        super().save(*args, **kwargs)
