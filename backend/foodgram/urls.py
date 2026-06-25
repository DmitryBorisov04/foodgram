from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import SubscriptionViewSet

router = DefaultRouter()
router.register(r'users', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls)),
]
