import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.forms import ValidationError
from rest_framework import serializers, status

from constants import (
    MINIMUM_COOKING_TIME, MINIMUM_INGREDIENT_AMOUNT,
    MAXIMUM_INGREDIENT_AMOUNT, MAXIMUM_COOKING_TIME
)
from recipes.models import (
    Favourite, Follow, Ingredient, IngredientsAmount, Recipe,
    ShoppingCart, Tag
)
from users.validators import ValidateUsername

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализотр для закодирования изображения в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='temp.' + ext
            )
        return super().to_internal_value(data)


class UserCreateSerializer(
    ValidateUsername, serializers.ModelSerializer
):
    """Сериализатор для регистрации User."""

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализтор для модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя."""
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.following.filter(user=obj).exists()


class FollowingSerializer(serializers.ModelSerializer):
    """Сериализатор для получения списка подписок пользователя."""

    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )
        read_only_fields = (
            'email', 'username', 'first_name', 'last_name',
        )

    def validate(self, data):
        """Проверка подписок пользователя."""
        following = self.instance
        user = self.context.get('request').user
        if user.follower.filter(following=following).exists():
            raise ValidationError(
                'Вы уже подписаны.',
                code=status.HTTP_400_BAD_REQUEST)
        if user == following:
            raise ValidationError(
                'Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST)
        return data

    def get_is_subscribed(self, obj):
        """Проверка подписан ли пользователь."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user,
                following=obj).exists()
        return False

    def get_recipes(self, obj):
        """Берём рецепты пользователя."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = ShortRecipeCellSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Определяем количество рецептов."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class ShortRecipeCellSerializer(serializers.ModelSerializer):
    """Сериализатор для маленькой ячейки рецепта."""

    image = Base64ImageField(
        required=False,
        allow_null=True
    )
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'units_measurement')


class IngredientsAmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели IngredientsAmount для связи между таблицами
    Recipe и Ingreduent.
    """

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    units_measurement = serializers.ReadOnlyField(
        source='ingredient.units_measurement'
    )

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'name', 'units_measurement', 'amount')


class GetRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe."""

    tags = TagSerializer(
        many=True
    )
    author = UserSerializer()
    ingredients = IngredientsAmountSerializer(
        many=True,
        source='recipes_amount'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверка на нахождение рецепта в списке избранного."""
        return (
            self.context.get('request').user.is_authenticated
            and Favourite.objects.filter(
                user=self.context['request'].user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверка на нахождение рецепта в списке покупок."""

        return (self.context.get('request').user.is_authenticated
                and ShoppingCart.objects
                .filter(user=self.context['request'].user,
                        recipe=obj).exists())


class AddIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения полей при создании Recipe."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MINIMUM_INGREDIENT_AMOUNT,
        max_value=MAXIMUM_INGREDIENT_AMOUNT,
    )

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'amount',)


class PostRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания Recipe."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = AddIngredientsSerializer(
        many=True)
    cooking_time = serializers.IntegerField(
        min_value=MINIMUM_COOKING_TIME,
        max_value=MAXIMUM_COOKING_TIME,
    )
    image = Base64ImageField(
        required=False,
        allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_tags(self, value):
        """Функция проверки наличия тегов и отсутствия их повторений."""
        if not value:
            raise serializers.ValidationError(
                'Добавьте тег.'
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError(
                'Найдены повторяющиеся теги.'
            )

        return value

    def validate_ingredients(self, value):
        """Функция проверки наличия ингредиентов и отсутствия их повторений."""
        if not value:
            raise serializers.ValidationError(
                'Добавьте ингредиент.'
            )
        ingredients = [item['id'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError([{
                'ingredients': ['Ингридиенты не должны повторяться.']
            }])
        existing_ingredients = Ingredient.objects.filter(id__in=ingredients)
        existing_ids = set(
            [ingredient.id for ingredient in existing_ingredients]
        )
        non_existing_ids = set(ingredients) - existing_ids
        if non_existing_ids:
            raise serializers.ValidationError({
                'ingredients': [
                    'Следующие ингредиенты не существуют: {}'
                    .format(non_existing_ids)]
            })
        return value

    def add_items(self, ingredients, recipe):
        """Функция добавления ингредиентов в рецепт."""
        IngredientsAmount.objects.bulk_create([IngredientsAmount(
            recipe=recipe,
            ingredient_id=ingredient.get('id'),
            amount=ingredient.get('amount'),
        ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        """Функция создания рецепта на основе валидированных данных."""
        if 'image' not in validated_data:
            raise serializers.ValidationError(
                'Добавьте изображение.'
            )
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_items(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Функция обновления рецепта на основе валидированных данных."""
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.add_items(ingredients, instance)
        else:
            raise serializers.ValidationError(
                'Поле "ingredients" обязательно.'
            )
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        else:
            raise serializers.ValidationError(
                'Поле "tags" обязательно.'
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Функция для показа страницы с рецептом после его создания."""
        return GetRecipeSerializer(
            instance, context={
                'request': self.context.get('request')
            }).data


class FavouriteSerializer(serializers.ModelSerializer):
    """Серилизатор для избранных рецептов."""

    class Meta:
        model = Favourite
        fields = ('recipe', 'user')

    def validate(self, data):
        """Функция для проверки дубликатов всписке избранного."""
        user = data['user']
        if user.favourites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном.'
            )
        return data
