from django.db.models import Sum
from django.utils import timezone

from recipes.models import Product, Recipe

MONTHS = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


def get_report_date():
    date = timezone.localdate()
    return f'{date.day:02d} {MONTHS[date.month]} {date.year}'


def get_shopping_cart_text(user):
    products = Product.objects.filter(
        recipe_products__recipe__shoppingcarts__user=user,
    ).values(
        'name',
        'measurement_unit',
    ).annotate(
        total_amount=Sum('recipe_products__amount'),
    ).order_by('name')

    recipes = Recipe.objects.filter(
        shoppingcarts__user=user,
    ).select_related(
        'author',
    ).prefetch_related(
        'tags',
    ).order_by('name')

    return '\n'.join([
        'Список покупок',
        f'Дата составления: {timezone.localdate().strftime("%d.%m.%Y")}',
        '',
        'Продукты:',
        *[
            (
                f'{number}. '
                f'{product["name"][:1].upper() + product["name"][1:]} '
                f'({product["measurement_unit"]}) — '
                f'{product["total_amount"]}'
            )
            for number, product in enumerate(products, start=1)
        ],
        '',
        'Рецепты:',
        *[
            (
                f'{number}. {recipe.name} — '
                f'автор: {recipe.author.username}'
                f'{f" | теги: {", ".join(tag.name for tag in recipe.tags.all())}" if recipe.tags.exists(
                ) else ""}'
            )
            for number, recipe in enumerate(recipes, start=1)
        ],
    ])
