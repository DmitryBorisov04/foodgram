from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
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

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    ProductSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        if self.action in (
            'me',
            'avatar',
            'set_password',
            'subscriptions',
            'subscribe',
        ):
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'avatar':
            return AvatarSerializer
        if self.action == 'subscriptions':
            return SubscriptionUserSerializer
        if self.action in ('list', 'retrieve', 'me'):
            return UserSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=('get',))
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribers__user=request.user,
        ).order_by('id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionUserSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionUserSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=True, methods=('post', 'delete'))
    def subscribe(self, request, pk=None, id=None):
        user = request.user
        author = get_object_or_404(User, id=id or pk)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscriptionUserSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author,
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы не были подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar')
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_products__product',
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.create_or_delete_relation(
            model=Favorite,
            request=request,
            recipe=recipe,
            exists_message='Рецепт уже в избранном.',
            missing_message='Рецепта не было в избранном.',
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.create_or_delete_relation(
            model=ShoppingCart,
            request=request,
            recipe=recipe,
            exists_message='Рецепт уже в списке покупок.',
            missing_message='Рецепта не было в списке покупок.',
        )

    @staticmethod
    def create_or_delete_relation(
        model,
        request,
        recipe,
        exists_message,
        missing_message,
    ):
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'errors': exists_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': missing_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        cart_items = ShoppingCart.objects.filter(
            user=request.user,
        ).select_related('recipe', 'recipe__author')

        if not cart_items.exists():
            return Response(
                {'errors': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = Product.objects.filter(
            recipe_products__recipe__shopping_cart__user=request.user,
        ).values(
            'name',
            'measurement_unit',
        ).annotate(
            total_amount=Sum('recipe_products__amount'),
        ).order_by('name')

        lines = [
            f'Список покупок для {request.user.get_full_name()}',
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
            name = product['name']
            unit = product['measurement_unit']
            amount = product['total_amount']
            lines.append(f'{index}. {name} ({unit}) — {amount}')

        response = HttpResponse(
            '\n'.join(lines),
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
