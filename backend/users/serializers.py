from .models import User, Subscription
from rest_framework import serializers
from djoser.serializers import (UserCreateSerializer, UserSerializer)


class UserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name',
                  'username', 'email', 'avatar')


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name', 'avatar', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author')
