def build_shopping_list(user, cart_items, products):
    lines = [
        f'Список покупок для {user.get_full_name()}',
        '',
        'Рецепты:',
    ]

    for index, item in enumerate(cart_items, start=1):
        lines.append(
            f'{index}. {item.recipe.name} '
            f'({item.recipe.cooking_time} мин.)'
        )

    lines.extend(['', 'Продукты:'])

    for index, product in enumerate(products, start=1):
        lines.append(
            f'{index}. {product["name"]} '
            f'({product["measurement_unit"]}) — '
            f'{product["total_amount"]}'
        )

    return '\n'.join(lines)
