from collections import Counter

from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField


from recipes.models import (
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Tag,
    User,
    Subscription,
)

MIN_VALUE_AMOUNT = 1
MIN_VALUE_COOKING_TIME = 1


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields: tuple[str, ...] = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj,
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='product.id')
    name = serializers.CharField(source='product.name')
    measurement_unit = serializers.CharField(
        source='product.measurement_unit'
    )

    class Meta:
        model = RecipeProduct
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeProductSerializer(
        many=True,
        read_only=True,
        source='recipe_products',
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def _is_recipe_in_user_list(self, model, recipe):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=recipe,
            ).exists()
        )

    def get_is_favorited(self, obj):
        return self._is_recipe_in_user_list(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._is_recipe_in_user_list(ShoppingCart, obj)


class ProductAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE_AMOUNT)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = ProductAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список продуктов не может быть пустым.'
            )

        products = [item['id'] for item in value]
        product_ids = [product.id for product in products]

        duplicate_ids = [
            product_id
            for product_id, count in Counter(product_ids).items()
            if count > 1
        ]

        if duplicate_ids:
            duplicate_names = [
                product.name
                for product in products
                if product.id in duplicate_ids
            ]
            duplicate_names = sorted(set(duplicate_names))

            raise serializers.ValidationError(
                'Продукты не должны повторяться: '
                f'{", ".join(duplicate_names)}.'
            )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список тегов не может быть пустым.'
            )

        tag_ids = [tag.id for tag in value]
        duplicate_ids = [
            tag_id
            for tag_id, count in Counter(tag_ids).items()
            if count > 1
        ]

        if duplicate_ids:
            duplicate_names = [
                tag.name
                for tag in value
                if tag.id in duplicate_ids
            ]
            duplicate_names = sorted(set(duplicate_names))

            raise serializers.ValidationError(
                'Теги не должны повторяться: '
                f'{", ".join(duplicate_names)}.'
            )

        return value

    def validate(self, attrs):
        if self.instance is not None:
            for field in ('ingredients', 'tags'):
                if field not in self.initial_data:
                    raise serializers.ValidationError(
                        {field: 'Это поле обязательно.'}
                    )
        return attrs

    @staticmethod
    def create_products(recipe, products_data):
        RecipeProduct.objects.bulk_create(
            RecipeProduct(
                recipe=recipe,
                product=product_data['id'],
                amount=product_data['amount'],
            )
            for product_data in products_data
        )

    def create(self, validated_data):
        products_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.create_products(recipe, products_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            products_data = validated_data.pop('ingredients')
            instance.recipe_products.all().delete()
            self.create_products(instance, products_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True,
    )

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes = recipes[:int(recipes_limit)]
                except (TypeError, ValueError):
                    pass
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data
