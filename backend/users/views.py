from .serializers import (UserSerializer,
                          UserCreateSerializer,
                          SubscriptionSerializer)
from .models import User, Subscription
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class SubscriptionViewSet(viewsets.ModelViewSet):
    required_permissions = [IsAuthenticated]

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if user != author:
                subscription, created = Subscription.objects.get_or_create(
                    user=user, author=author)
                if created:
                    serializer = self.get_serializer(subscription)
                    return Response(serializer.data, status=201)
                else:
                    return Response({'detail': 'Вы уже подписаны на этого автора.'}, status=400)
            else:
                return Response({'detail': 'Вы не можете подписаться на самого себя.'}, status=400)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author=author).first()
            if subscription:
                subscription.delete()
                return Response({'detail': 'Вы успешно отписались от автора.'}, status=204)
            else:
                return Response({'detail': 'Вы не подписаны на этого автора.'}, status=400)


class SubscriptionListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscriptions__user=user)
