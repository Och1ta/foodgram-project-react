from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

from recipes.constants import MAX_AMOUNT, MIN_AMOUNT
from recipes.models import (AmountIngredient, Favorite, Ingredient,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription, User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email',
            'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and request.user.followed_users.filter(author=obj).exists()
        )


class SubscribeSerializer(UserSerializer):
    """Serializer for subscriptions."""

    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields)
        fields.extend(['recipes', 'recipes_count'])
        read_only_fields = (
            'email', 'username', 'first_name', 'last_name'
        )

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        recipes = RecipeShortSerializer(
            queryset, many=True,
            context=self.context
        )
        return recipes.data


class SubscribeCreateSerializer(serializers.ModelSerializer):
    """Serializer for subscription creating."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        author_id = data.get('author').id
        user_id = data.get('user').id
        if user_id == author_id:
            raise serializers.ValidationError(
                detail='Нельзя подписаться на себя',
                code=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(
                author=author_id,
                user=user_id).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписались',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        return SubscribeSerializer(
            instance=instance.author,
            context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class AmountIngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients amount."""

    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateAmountIngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient amount creation."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'min_value': f'Нужно больше чем {MIN_AMOUNT}.',
            'max_value': f'Нужно меньше чем {MAX_AMOUNT}'}
    )

    class Meta:
        fields = ('id', 'amount')
        model = AmountIngredient


class RecipeReadSerializer(serializers.ModelSerializer):
    """Serializer for recipe reading."""

    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = AmountIngredientSerializer(
        many=True,
        source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'text', 'cooking_time', 'image',
            'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        """Проверка на нахождение рецепта в списке избранного."""
        request = self.context.get('request')
        is_favorited = (
            request.user.is_authenticated and getattr(
                request.user,
                'recipes_favorite_related'
            ).filter(recipe=obj).exists())
        return is_favorited

    def get_is_in_shopping_cart(self, obj):
        """Проверка на нахождение рецепта в списке покупок."""
        request = self.context.get('request')
        is_in_shopping_cart = (
            request.user.is_authenticated and getattr(
                request.user,
                'recipes_shoppingcart_related'
            ).filter(recipe=obj).exists())
        return is_in_shopping_cart


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for recipe creation."""

    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateAmountIngredientSerializer(
        many=True,
        write_only=True
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'min_value': f'Времени нужно больше чем {MIN_AMOUNT}.',
            'max_value': f'Времени нужно меньше чем {MAX_AMOUNT}'
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'text', 'cooking_time', 'image',
            'tags', 'author', 'ingredients'
        )

    def validate(self, data):
        if not data.get('image'):
            raise serializers.ValidationError(
                detail='Должно быть изображение',
                code=status.HTTP_400_BAD_REQUEST
            )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                detail='Должны быть теги',
                code=status.HTTP_400_BAD_REQUEST
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                detail='Теги не должны повторяться',
                code=status.HTTP_400_BAD_REQUEST
            )
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                detail='Должны быть ингредиенты',
                code=status.HTTP_400_BAD_REQUEST
            )
        if (len(set(item['id'] for item in ingredients))
                != len(ingredients)):
            raise serializers.ValidationError(
                detail='Ингредиенты не должны повторяться',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        create_ingredients = [
            AmountIngredient(
                recipe=recipe, ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients]
        AmountIngredient.objects.bulk_create(create_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        current_user = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=current_user)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for recipe short view."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class UserRecipeRelationSerializer(serializers.ModelSerializer):
    """Abstract sterilizer for favorites and shopping list."""

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        user_id = data.get('user').id
        recipe_id = data.get('recipe').id
        if self.Meta.model.objects.filter(user=user_id,
                                          recipe=recipe_id).exists():
            raise serializers.ValidationError('Рецепт уже был добавлен')
        return data

    def to_representation(self, instance):
        serializer = RecipeShortSerializer(
            instance.recipe, context=self.context)
        return serializer.data


class ShoppingCartCreateDeleteSerializer(UserRecipeRelationSerializer):
    """Serializer for shopping cart."""

    class Meta(UserRecipeRelationSerializer.Meta):
        model = ShoppingCart


class FavoriteCreateDeleteSerializer(UserRecipeRelationSerializer):
    """Serializer for favorite recipes."""

    class Meta(UserRecipeRelationSerializer.Meta):
        model = Favorite
