import base64
import binascii

from django.core.files.base import ContentFile
from rest_framework import serializers

from carts.models import Favorite, ShoppingCart
from users.serializers import UserSerializer
from .models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients',
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists()
        return False


class IngredientsAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = serializers.CharField(allow_blank=False)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'cooking_time',
            'image', 'ingredients', 'tags',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым.'
            )
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список тегов не может быть пустым.'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Изображение не может быть пустым.'
            )
        if ';base64,' not in value:
            raise serializers.ValidationError(
                'Некорректный формат изображения.'
            )
        return value

    def validate(self, attrs):
        if self.instance is not None:
            for field in ('ingredients', 'tags'):
                if field not in self.initial_data:
                    raise serializers.ValidationError({
                        field: 'Это поле обязательно.'
                    })
        return attrs

    def _decode_image(self, image_data):
        try:
            file_format, imgstr = image_data.split(';base64,')
            ext = file_format.split('/')[-1]
            return ContentFile(
                base64.b64decode(imgstr),
                name=f'recipe.{ext}',
            )
        except (TypeError, ValueError, binascii.Error):
            raise serializers.ValidationError({
                'image': 'Некорректный формат изображения.'
            })

    def _create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients_data
        )

    def create(self, validated_data):
        image_data = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = validated_data.pop('author', self.context['request'].user)

        recipe = Recipe.objects.create(
            author=author,
            image=self._decode_image(image_data),
            **validated_data,
        )
        self._create_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        image_data = validated_data.pop('image', None)
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image_data is not None:
            instance.image = self._decode_image(image_data)

        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self._create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
