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
    MIN_PRODUCT_AMOUNT,
    MIN_COOKING_TIME,
)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields: tuple[str, ...] = (
            *DjoserUserSerializer.Meta.fields,
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

    def get_is_favorited(self, recipe):
        return self._is_recipe_in_user_list(Favorite, recipe)

    def get_is_in_shopping_cart(self, recipe):
        return self._is_recipe_in_user_list(ShoppingCart, recipe)


class ProductAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    amount = serializers.IntegerField(min_value=MIN_PRODUCT_AMOUNT)


class RecipeWriteSerializer(serializers.ModelSerializer):

    EMPTY_LIST_ERROR = 'Список {items} не может быть пустым.'
    DUPLICATE_ITEMS_ERROR = '{items} не должны повторяться: {duplicates}.'

    ingredients = ProductAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

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

    def _validate_unique_items(
        self,
        value,
        items,
        empty_items_name,
        duplicate_items_name,
    ):
        if not value:
            raise serializers.ValidationError(
                self.EMPTY_LIST_ERROR.format(items=empty_items_name)
            )

        item_ids = [item.id for item in items]
        duplicate_ids = {
            item_id
            for item_id, count in Counter(item_ids).items()
            if count > 1
        }

        if duplicate_ids:
            duplicate_names = {
                item.name
                for item in items
                if item.id in duplicate_ids
            }
            raise serializers.ValidationError(
                self.DUPLICATE_ITEMS_ERROR.format(
                    items=duplicate_items_name,
                    duplicates=duplicate_names,
                )
            )

        return value

    def validate_ingredients(self, value):
        return self._validate_unique_items(
            value=value,
            items=[item['id'] for item in value],
            empty_items_name='продуктов',
            duplicate_items_name='Продукты',
        )

    def validate_tags(self, value):
        return self._validate_unique_items(
            value=value,
            items=value,
            empty_items_name='тегов',
            duplicate_items_name='Теги',
        )

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
        tags = validated_data.pop('tags')
        products_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user

        recipe = super().create(validated_data)
        self.create_products(recipe, products_data)
        recipe.tags.set(tags)

        return recipe

    def update(self, instance, validated_data):
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

    def get_recipes(self, recipes_data):
        request = self.context.get('request')
        recipes = recipes_data.recipes.all()
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
