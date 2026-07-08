from django.contrib import admin
from .models import Recipe, RecipeIngredient, RecipeTag, Ingredient, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'created_at', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline, RecipeTagInline]

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()
