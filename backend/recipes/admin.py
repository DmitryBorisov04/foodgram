from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count

from .models import (
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = (
        'is_staff',
        'is_active',
        'date_joined',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_total=Count('recipes', distinct=True),
            subscribers_total=Count('subscribers', distinct=True),
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes_total

    @admin.display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.subscribers_total


class RecipeProductInline(admin.TabularInline):
    model = RecipeProduct
    extra = 1
    autocomplete_fields = ('product',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorites_count',
        'shopping_cart_count',
        'products_count',
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    list_filter = (
        'tags',
        'author',
        'created_at',
    )
    autocomplete_fields = ('author', 'tags')
    inlines = (RecipeProductInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related('tags')

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='В списках покупок')
    def shopping_cart_count(self, obj):
        return obj.shopping_cart.count()

    @admin.display(description='Продуктов')
    def products_count(self, obj):
        return obj.recipe_products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        'recipes_count',
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipes_total=Count('recipes'))

    @admin.display(description='В рецептах')
    def recipes_count(self, obj):
        return obj.recipes_total


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'recipes_count',
    )
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipes_total=Count('recipes'))

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes_total


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'author__username',
        'author__email',
    )
    list_filter = ('created_at',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'recipe_author', 'created_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created_at',)

    @admin.display(description='Автор рецепта')
    def recipe_author(self, obj):
        return obj.recipe.author


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
        'recipe_author',
        'recipe_cooking_time',
        'recipe_products_count',
        'created_at',
    )
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('created_at', 'recipe__tags')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe', 'recipe__author')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, obj):
        return obj.recipe.author

    @admin.display(description='Время готовки')
    def recipe_cooking_time(self, obj):
        return obj.recipe.cooking_time

    @admin.display(description='Продуктов в рецепте')
    def recipe_products_count(self, obj):
        return obj.recipe.recipe_products.count()
