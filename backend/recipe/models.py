import re

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.forms import ValidationError


User = get_user_model()


class Ingredient(models.Model):
    """Ingredient model."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название ингридиента')
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Едeницы измерения')

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Tag(models.Model):
    """Tag model."""

    GREEN = '#03c03c'
    RED = '#ff6347'
    BLUE = '#120a8f'
    TAG_COLOR_CODE = [
        (GREEN, 'Зеленый'),
        (RED, 'Красный'),
        (BLUE, 'Синий'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Название тэга'
    )
    color = models.CharField(
        max_length=7,
        choices=TAG_COLOR_CODE,
        verbose_name='Цветовой код'
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='Уникальный слаг'
    )

    def __str__(self):
        return f'{self.name}'

    def check_color(self):
        """Проверяем соответствие и формат цветового кода."""

        if self.color not in [choice[0] for choice in self.TAG_COLOR_CODE]:
            raise ValidationError('Недопустимый цвет')

        if not re.match(r'^#[a-fA-F0-9]{6}$', self.color):
            raise ValidationError('Неверный формат цветового кода')


class Recipe(models.Model):
    """Recipe model."""

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsAmount',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Имя автора'
    )
    image = models.ImageField(
        upload_to='images/',
        verbose_name='Изображение блюда'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    text = models.TextField(
        max_length=500,
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField(
        default=1,
        validators=(
            MinValueValidator(1),
            MaxValueValidator(240),
        ),
        verbose_name='Время приготовления в минутах'
    )

    def __str__(self):
        return f'{self.name}'


class IngredientsAmount(models.Model):
    """Модель посредник для связи моделей Recipe и Ingredient."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes_amount',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveIntegerField(
        default=1,
        validators=(
            MinValueValidator(1),
            MaxValueValidator(1000),
        ),
        verbose_name='Количество',
    )

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}: {self.amount}'


class ShoppingCart(models.Model):
    """ShoppingCart model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
        related_name='shop_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_recipe',
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(models.Model):
    """Favourites model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
        related_name='favourites',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'{self.user} - {self.recipe}'
