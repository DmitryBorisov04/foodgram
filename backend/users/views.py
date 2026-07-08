import base64
import binascii

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import (
    SubscriptionSerializer,
    SubscriptionUserSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    @action(detail=True, methods=('post', 'delete'))
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

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


class CustomUserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        if self.action in ('me', 'avatar', 'set_password', 'subscriptions'):
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'subscriptions':
            return SubscriptionUserSerializer
        if self.action in ('list', 'retrieve', 'me'):
            return UserSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == 'me':
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all().order_by('id')

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribers__user=request.user).order_by('id')
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

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar')
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'errors': 'Аватар не предоставлен.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if isinstance(avatar_data, str) and ';base64,' in avatar_data:
                try:
                    file_format, imgstr = avatar_data.split(';base64,')
                    ext = file_format.split('/')[-1]
                    user.avatar = ContentFile(
                        base64.b64decode(imgstr),
                        name=f'avatar.{ext}',
                    )
                except (TypeError, ValueError, binascii.Error):
                    return Response(
                        {'errors': 'Некорректный формат изображения.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                user.avatar = avatar_data

            user.save()
            return Response({
                'avatar': request.build_absolute_uri(user.avatar.url)
                if user.avatar else None
            })

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
