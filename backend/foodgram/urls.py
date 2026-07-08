from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet, SubscriptionViewSet
from recipes.views import IngredientViewSet, TagViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls)),

    path('api/users/<int:pk>/subscribe/',
         SubscriptionViewSet.as_view(
             {'post': 'subscribe', 'delete': 'subscribe'})
         ),
]
