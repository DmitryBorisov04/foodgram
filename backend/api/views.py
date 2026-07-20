from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Product,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)
from .filters import RecipeFilter, ProductFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    ProductSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionUserSerializer,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            author_subscriptions__user=request.user
        )

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(
            self.get_serializer(page, many=True).data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionUserSerializer,
    )
    def subscribe(self, request, pk=None):
        user = request.user

        if request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=user,
                author_id=pk,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, pk=pk)

        if user == author:
            raise ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'}
            )

        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author,
        )

        if not created:
            raise ValidationError(
                {'errors': f'Вы уже подписаны на пользователя {author.username}.'}
            )

        return Response(
            self.get_serializer(author).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        serializer_class=AvatarSerializer,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_products__product',
    ).order_by('-created_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound(f'Рецепт с id {pk} не найден.')

        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse('short-link', kwargs={'recipe_id': pk})
                )
            }
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self.create_or_delete_relation(
            model=Favorite,
            request=request,
            recipe_id=pk,
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self.create_or_delete_relation(
            model=ShoppingCart,
            request=request,
            recipe_id=pk,
        )

    @staticmethod
    def create_or_delete_relation(model, request, recipe_id):
        if request.method == 'DELETE':
            get_object_or_404(
                model,
                user=request.user,
                recipe_id=recipe_id,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, pk=recipe_id)

        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )

        if not created:
            raise ValidationError(
                {
                    'errors': (
                        f'{model._meta.verbose_name.capitalize()} '
                        f'«{recipe.name}» уже существует.'
                    )
                }
            )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        products = Product.objects.filter(
            recipe_products__recipe__shoppingcarts__user=request.user,
        ).values(
            'name',
            'measurement_unit',
        ).annotate(
            total_amount=Sum('recipe_products__amount'),
        ).order_by('name')

        lines = ['Список покупок', '']

        for product in products:
            lines.append(
                f'{product["name"]} '
                f'({product["measurement_unit"]}) — '
                f'{product["total_amount"]}'
            )

        response = HttpResponse(
            '\n'.join(lines),
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
