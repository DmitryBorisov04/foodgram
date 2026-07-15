from django.utils import timezone


def build_shopping_list(user, cart_items, products):
    recipe_lines = [
        (
            f'{index}. {item.recipe.name} '
            f'({item.recipe.cooking_time} мин.)'
        )
        for index, item in enumerate(cart_items, start=1)
    ]

    product_lines = [
        (
            f'{index}. {product["name"].capitalize()} '
            f'({product["measurement_unit"]}) — '
            f'{product["total_amount"]}'
        )
        for index, product in enumerate(products, start=1)
    ]

    return '\n'.join(
        [
            f'Список покупок для {user.get_full_name()}',
            f'Дата составления: {timezone.localdate().strftime("%d.%m.%Y")}',
            '',
            'Рецепты:',
            *recipe_lines,
            '',
            'Продукты:',
            *product_lines,
        ]
    )
