from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe

from .models import Favorite, ShoppingCart


class FavoriteViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if recipe.author == request.user:
            return Response(
                {
                    'errors': (
                        'Вы не можете добавить свой рецепт в избранное.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            return Response(status=status.HTTP_201_CREATED)

        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()

        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if recipe.author == request.user:
            return Response(
                {
                    'errors': (
                        'Вы не можете добавить свой рецепт '
                        'в список покупок.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            return Response(status=status.HTTP_201_CREATED)

        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()

        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartDownload(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        cart_items = ShoppingCart.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response(
                {'errors': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ingredients = cart_items.values(
            'recipe__recipe_ingredients__ingredient__name',
            'recipe__recipe_ingredients__ingredient__measurement_unit',
        ).annotate(
            total_amount=Sum('recipe__recipe_ingredients__amount')
        )

        text = 'Список покупок:\n\n'

        for item in ingredients:
            name = item['recipe__recipe_ingredients__ingredient__name']
            unit = item[
                'recipe__recipe_ingredients__ingredient__measurement_unit'
            ]
            amount = item['total_amount']
            text += f'{name} ({unit}) — {amount}\n'

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
