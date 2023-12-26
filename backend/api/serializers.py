from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.constants import (
    MAX_LENGTH_NAME, MAXIMUM_COOKING_TIME, MINIMUM_COOKING_TIME
)
from recipe.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe,
    ShoppingCart, Tag
)
from users.models import Subscription


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Serializer for Custom User"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Функция проверки подписки"""
        request = self.context['request']
        if not request.user.is_authenticated or request.user == obj:
            return False
        if not hasattr(obj, 'is_subscribed'):
            return obj.subscribers.filter(user=request.user).exists()
        return obj.is_subscribed


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for Create Custom User"""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password'
        )


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для управления подписками."""
    email = serializers.EmailField(
        source='author.email',
        read_only=True
    )
    id = serializers.IntegerField(
        source='author.id',
        read_only=True
    )
    username = serializers.CharField(
        source='author.username',
        read_only=True
    )
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context['request']
        try:
            recipes_limit = int(request.query_params.get('recipes_limit'))
        except Exception:
            recipes_limit = None
        queryset = obj.author.recipes.all()
        if recipes_limit is not None and recipes_limit > 0:
            queryset = queryset[:recipes_limit]
        return ShortRecipeSerializer(
            queryset, many=True, context=self.context
        ).data

    def get_is_subscribed(self, obj):
        request = self.context['request']
        field = 'is_subscribed'
        if not hasattr(obj, field):
            return obj.user == request.user
        return obj.is_subscribed

    def get_recipes_count(self, obj):
        field = 'recipes_count'
        if not hasattr(obj, field):
            return obj.author.recipes.count()
        return obj.recipes_count

    def validate(self, attrs):
        user = self.context['request'].user
        author_id = int(self.context['view'].kwargs.get('id'))
        if Subscription.objects.filter(user=user, author=author_id).exists():
            raise serializers.ValidationError(
                'Подписка уже существует.'
            )
        if author_id == user.id:
            raise serializers.ValidationError(
                'Пользователь не может подписаться на себя.'
            )
        return attrs

    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.is_subscribed = True
        return obj


class TagSerializer(serializers.ModelSerializer):
    """
    Tag Serializer.
    Обрабатывает только GET запросы.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Ingredient Serializer.
    Обрабатывает только GET запросы.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for the recipe of ingredients
    of the M2M link model between tables.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientInRecipe.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAddAmountSerializer(serializers.ModelSerializer):
    """Serializer for IngredientAddAmount model."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for read Recipe model."""

    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_recipe',
        many=True,
        read_only=True, )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        """Проверка на нахождение рецепта в списке избранного."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка на нахождение рецепта в списке покупок."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class AddRecipeSerializer(serializers.ModelSerializer):
    """Serializer for Adding Recipe"""

    ingredients = IngredientAddAmountSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    name = serializers.CharField(max_length=MAX_LENGTH_NAME)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'text'),
                message='Рецепт уже существует!'
            )
        ]

    def validate_ingredients(self, ingredients):
        """
        Функция проверки наличия ингредиентов и отсутствия их повторений.
        """
        if not ingredients:
            raise serializers.ValidationError(
                'Поле ингредиентов не может быть пустым!')
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Число игредиентов должно быть больше 0.')
        ingrs = [item['id'] for item in ingredients]
        if len(ingrs) != len(set(ingrs)):
            raise serializers.ValidationError(
                'В рецепте не может быть повторяющихся ингредиентов!')
        return ingredients

    def validate_cooking_time(self, data):
        """Функция проверки наличия времени приготовления."""
        if data <= MINIMUM_COOKING_TIME:
            raise serializers.ValidationError(
                'Блюдо не может готовиться меньше или 1 минуту.'
            )
        if data > MAXIMUM_COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления должно быть меньше 240!.'
            )
        return data

    def validate_tags(self, data):
        """Функция проверки наличия тегов"""
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Поле тэгов не может быть пустым!.'
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredient_list = [
            IngredientInRecipe(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        """
        Создаем рецепт на основе валидированных данных.
        Настроенна проверка что если при создании рецепта значение поля 'image'
        пустое или не передано будет выброшено исключениет.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        """Обновление рецепта на основе валидированных данных."""
        recipe.ingredients.clear()
        recipe.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, value):
        serializer = RecipeSerializer(value, context=self.context)
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Serializer for displaying a Short Recipe"""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Favorite model."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user, recipe = data.get('user'), data.get('recipe')
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном!')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShortRecipeSerializer(instance.recipe, context=context).data


class ShoppingCartSerializer(FavoriteSerializer):
    """Serializer for Shopping Cart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user_id = data.get('user').id
        recipe_id = data.get('recipe').id
        if self.Meta.model.objects.filter(user=user_id,
                                          recipe=recipe_id).exists():
            raise serializers.ValidationError('Рецепт уже добавлен в список.')
        return data

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(
            instance.recipe, context=self.context)
        return serializer.data


class RecipeForUserSerializer(serializers.ModelSerializer):
    """Serializer for communication between the Recipe and the User."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
