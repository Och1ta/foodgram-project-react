from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from constants import (
    MAX_LENGTH_INGRIDIENT_NAME, MAX_LENGTH_UNITS_MEASURE,
    MAX_LENGTH_TAG_NAME, MAX_LENGTH_SLUG, MAX_LENGTH_COLOR,
    MAX_LENGTH_RECIPE
)

User = get_user_model()


class Ingredient(models.Model):
    """Абстрактная модель класса Ингредиента"""

    name = models.CharField(
        max_length=MAX_LENGTH_INGRIDIENT_NAME,
        blank=False,
        verbose_name='Название'
    )
    units_measurement = models.CharField(
        max_length=MAX_LENGTH_UNITS_MEASURE,
        blank=False,
        verbose_name='Еденицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Абстрактная модель класса Тега"""
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        blank=False,
        verbose_name='Название'
    )
    color_code = models.CharField(
        max_length=MAX_LENGTH_COLOR,
        unique=True,
        blank=False,
        verbose_name='Цвет',
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        blank=False,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipies/images/',
        null=True,
        blank=True,
        verbose_name='Изображение рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngridientInRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='tags',
        verbose_name='Теги'
    )
    cooking_time = models.IntegerField(
        blank=False,
        validators=(
            MinValueValidator(1),
            MaxValueValidator(240),
        ),
        verbose_name='Время приготовления рецепта'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Модель корзины."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'


class Favorite(models.Model):
    """Модель добавления рецепта в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class IngredientsAmount(models.Model):
    """Абстрактная модель посредник для связи между Recipe и Ingredient."""

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