from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    MIN_COOKING_TIME,
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class RecipesCountAdminMixin:
    list_display = ('recipes_count',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_total=Count('recipes', distinct=True),
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes_total


class HasRelatedFilter(admin.SimpleListFilter):
    related_name: str | None = None
    choices = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.choices

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()

        if self.value() == 'no':
            return queryset.filter(
                **{f'{self.related_name}__isnull': True}
            )

        return queryset


class HasRecipesFilter(HasRelatedFilter):
    title = 'есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(HasRelatedFilter):
    title = 'есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscriptions'


class HasSubscribersFilter(HasRelatedFilter):
    title = 'есть подписчики'
    parameter_name = 'has_subscribers'
    related_name = 'subscribers'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'время готовки'
    parameter_name = 'cooking_time_group'

    FAST_LIMIT = 30
    MEDIUM_LIMIT = 60
    MAX_COOKING_TIME = 2_147_483_647

    def lookups(self, request, model_admin):
        self.ranges = {
            'fast': (MIN_COOKING_TIME, self.FAST_LIMIT - 1),
            'medium': (
                self.FAST_LIMIT,
                self.MEDIUM_LIMIT - 1,
            ),
            'long': (
                self.MEDIUM_LIMIT,
                self.MAX_COOKING_TIME,
            ),
        }

    def queryset(self, request, recipes):
        selected_range = self.ranges.get(self.value())

        if selected_range is None:
            return recipes

        return recipes.filter(
            cooking_time__range=selected_range
        )


@admin.register(User)
class UserAdmin(RecipesCountAdminMixin, DjangoUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        *RecipesCountAdminMixin.list_display,
        'subscriptions_count',
        'subscribers_count',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            subscriptions_total=Count('subscriptions', distinct=True),
            subscribers_total=Count(
                'author_subscriptions',
                distinct=True,
            ),
        )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return user.get_full_name()

    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if not user.avatar:
            return '-'
        return mark_safe(
            f'<img src="{user.avatar.url}" '
            f'width="50" height="50" '
            f'style="object-fit: cover; border-radius: 50%;" />'
        )

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions_total

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers_total


class RecipeProductInline(admin.TabularInline):
    model = RecipeProduct
    extra = 1
    autocomplete_fields = ('product',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorites_count',
        'products_display',
        'tags_display',
        'image_preview',
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'tags__name',
        'products__name',
    )
    list_filter = (
        'tags',
        'author',
        CookingTimeFilter,
    )
    autocomplete_fields = ('author', 'tags')
    inlines = (RecipeProductInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'author',
        ).prefetch_related(
            'tags',
            'recipe_products__product',
        ).annotate(
            favorites_total=Count('favorites', distinct=True),
        )

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites_total

    @admin.display(description='Продукты')
    def products_display(self, recipe):
        products = [
            (
                f'{recipe_product.product.name} — '
                f'{recipe_product.amount} '
                f'{recipe_product.product.measurement_unit}'
            )
            for recipe_product in recipe.recipe_products.all()
        ]

        return mark_safe('<br>'.join(products))

    @admin.display(description='Теги')
    def tags_display(self, recipe):
        return mark_safe(
            '<br>'.join(tag.name for tag in recipe.tags.all())
        )

    @admin.display(description='Картинка')
    def image_preview(self, recipe):
        if not recipe.image:
            return '-'
        return mark_safe(
            f'<img src="{recipe.image.url}" '
            f'width="80" height="80" '
            f'style="object-fit: cover;" />'
        )


@admin.register(Product)
class ProductAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        *RecipesCountAdminMixin.list_display,
    )
    search_fields = ('name',)
    list_filter = (
        'measurement_unit',
        HasRecipesFilter,
    )


@admin.register(Tag)
class TagAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        *RecipesCountAdminMixin.list_display,
    )
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'user__email',
        'author__username',
        'author__email',
    )


@admin.register(Favorite, ShoppingCart)
class RecipeRelationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'recipe',
        )
