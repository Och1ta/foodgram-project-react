from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Length

from recipes.constants import MAX_HEX, MAX_LEN_TITLE, MAX_AMOUNT, MIN_AMOUNT
from users.models import User


models.CharField.register_lookup(Length)


class Ingredient(models.Model):
    """Ingredient abstract model."""

    name = models.CharField(
        verbose_name='Ингридиент',
        max_length=MAX_LEN_TITLE,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=MAX_LEN_TITLE,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_unit'
            )
        ]

    def __str__(self):
        return '{} {}'.format(self.name, self.measurement_unit)


class Tag(models.Model):
    """Tag abstract model."""

    name = models.CharField(
        verbose_name='Название тeга',
        max_length=MAX_LEN_TITLE,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LEN_TITLE,
        unique=True,
    )
    color = ColorField(
        format='hex',
        max_length=MAX_HEX,
        default='#17A400',
        unique=True,
        verbose_name='Цвет в формате HEX'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тeг'
        verbose_name_plural = 'Тeги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe abstract model."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LEN_TITLE,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тeг',
        related_name='recipes',
        blank=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='recipes',
        through='AmountIngredient',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True,
        editable=False,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                limit_value=MIN_AMOUNT,
                message=f'Минимальное время {MIN_AMOUNT} минута!'),
            MaxValueValidator(
                limit_value=MAX_AMOUNT,
                message=f'Превысили максимальное время {MAX_AMOUNT} минут!'),
        ],
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = (
            models.CheckConstraint(
                check=models.Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
        )

    def __str__(self) -> str:
        return '{} {}'.format(self.name, self.author.username)


class AmountIngredient(models.Model):
    """
    The intermediary model is used to link the
    Recipe and Ingredient models.
    """

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredient',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингридиента',
        validators=(
            MinValueValidator(
                limit_value=MIN_AMOUNT,
                message=f'Минимальное значение {MIN_AMOUNT}!'),
            MaxValueValidator(
                limit_value=MAX_AMOUNT,
                message=f'Максимальное значение {MAX_AMOUNT}!')),
    )

    class Meta:
        verbose_name = 'Ингридиенты рецепта'
        verbose_name_plural = 'Ингридиенты рецептов'
        ordering = ('recipe',)

    def __str__(self):
        return (
            f'{self.ingredient.name} '
            f'({self.ingredient.measurement_unit}) - '
            f'{self.amount} '
        )


class UserRecipeRelation(models.Model):
    """Model for user-recipe relations."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_related',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_related',
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name=('\n%(app_label)s_%(class)s recipe already'
                      ' linked to this user\n'),
            ),
        )

    def __str__(self):
        return '{} {}'.format(self.user, self.recipe)


class Favorite(UserRecipeRelation):
    """Model for favorite recipes."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeRelation):
    """Model for shopping cart."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Cписок покупок'
        verbose_name_plural = 'Cписоки покупок'
