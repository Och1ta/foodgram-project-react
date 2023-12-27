from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

from recipe.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe,
    ShoppingCart, Tag
)
from users.models import Subscription, User

from api.constants import (
    MAXIMUM_COOKING_TIME, MINIMUM_COOKING_TIME, MINIMUM_AMOUNT,
    MAXIMUM_AMOUNT
)


class CustomUserSerializer(UserSerializer):
    """Serializer for Custom User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Subscription.objects.filter(
            user=user, author=obj.id).exists()
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for Create Custom User."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


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
        read_only_fields = '__all__',


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for the recipe of ingredients
    of the M2M link model between tables.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientInRecipe.objects.all())
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
    amount = serializers.IntegerField(
        min_value=MINIMUM_AMOUNT,
        max_value=MAXIMUM_AMOUNT
    )

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
        read_only=True,
    )
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

    ingredients = IngredientAddAmountSerializer(
        many=True,
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    name = serializers.CharField(max_length=200)
    cooking_time = serializers.IntegerField(
        min_value=MINIMUM_COOKING_TIME,
        max_value=MAXIMUM_COOKING_TIME
    )

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

    def validate(self, data):
        if not data.get('image'):
            raise serializers.ValidationError(
                detail='must be image',
                code=status.HTTP_400_BAD_REQUEST)
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                detail='must be tags',
                code=status.HTTP_400_BAD_REQUEST)
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                detail='tags should not by repeated',
                code=status.HTTP_400_BAD_REQUEST)
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                detail='must be ingredients',
                code=status.HTTP_400_BAD_REQUEST)
        if (len(set(item['id'] for item in ingredients))
            != len(ingredients)):
            raise serializers.ValidationError(
                detail='ingredients should not be repeated',
                code=status.HTTP_400_BAD_REQUEST)
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
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'ingredients' in validated_data:
            instance.ingredients.clear()
            self.create_ingredients(
                instance, validated_data.get('ingredients')
            )
        if 'tags' in validated_data:
            tags = validated_data.get('tags')
            instance.tags.set(tags)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Serializer for displaying a Short Recipe."""

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
        user_id = data.get('user').id
        recipe_id = data.get('recipe').id
        if self.Meta.model.objects.filter(user=user_id,
                                          recipe=recipe_id).exists():
            raise serializers.ValidationError('it has already been added')
        return data

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(
            instance.recipe, context=self.context)
        return serializer.data


class ShoppingCartSerializer(FavoriteSerializer):
    """Serializer for Shopping Cart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class RecipeForUserSerializer(serializers.ModelSerializer):
    """Serializer for communication between the Recipe and the User."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    """Serializer for Subscription model."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeForUserSerializer(recipes, many=True).data
