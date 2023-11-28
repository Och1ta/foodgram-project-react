from django.db import models

from constants import (
    MAX_LENGTH_INGRIDIENT_NAME, MAX_LENGTH_UNITS_MEASURE,
    MAX_LENGTH_TAG_NAME, MAX_LENGTH_SLUG, MAX_LENGTH_COLOR
)


class Ingredient(models.Model):
    """Абстрактная модель класса Ингредиента"""

    name = models.CharField(
        max_length=MAX_LENGTH_INGRIDIENT_NAME,
        blank=False,
        verbose_name='Название'
    )
    quantity = models.IntegerField(
        blank=False,
        verbose_name='Количество'
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
