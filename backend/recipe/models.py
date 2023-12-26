from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator
)
from django.db import models

from recipe.constants import (
    MINIMUM_COOKING_TIME, MAX_LENGTH_RECIPE_NAME, MAX_LENGTH_TAG_NAME,
    MAX_LENGTH_SLUG, MAX_LENGTH_UNIT_MEASURE, MAX_LENGTH_COLOR,
    MAXIMUM_COOKING_TIME, MINIMUM_COOKING_AMOUNT,
    MAXIMUM_INGREDIENT_AMOUNT, MAX_LENGTH_INGREDIENT_NAME
)


User = get_user_model()


class Ingredient(models.Model):
    """Ingridient abstract model."""
    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        verbose_name='Ингридиент'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_UNIT_MEASURE,
        verbose_name='Единицы измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag abstract model."""

    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Название тэга'
    )
    color = ColorField(
        format='hex',
        max_length=MAX_LENGTH_COLOR,
        default='#17A400',
        unique=True,
        verbose_name='Цвет в формате HEX'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe abstract model."""

    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME,
        verbose_name='Название'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги')
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='IngredientInRecipe',
        verbose_name='Ингридиенты в рецепте'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата'
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MINIMUM_COOKING_TIME,
                message='Минимальное время 1 минута!'),
            MaxValueValidator(
                MAXIMUM_COOKING_TIME,
                message='Превысили максимальное время 240 минут!'
            )
        ],
        verbose_name='Время приготовления (в минутах)',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель посредник для связи моделей Recipe и Ingredient."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_recipe',
        verbose_name='Ингридиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MINIMUM_COOKING_AMOUNT,
                message='Минимальное значение 1!'),
            MaxValueValidator(
                MAXIMUM_INGREDIENT_AMOUNT,
                message='Максимальное значение 1000!'
            )
        ],
        verbose_name='Количество ингридиента',
    )

    class Meta:
        verbose_name = 'Ингридиенты рецепта'
        verbose_name_plural = 'Ингридиенты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class AbsractUserRecipe(models.Model):
    """Abstract model for Favorite and ShoppingCart model"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s_user',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s_recipe',
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(AbsractUserRecipe):
    """Favourites abstract model."""

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_name_favorite'
            )
        ]


class ShoppingCart(AbsractUserRecipe):
    """ShoppingCart abstract model."""

    class Meta:
        verbose_name = 'Cписок покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart'
            )
        ]
