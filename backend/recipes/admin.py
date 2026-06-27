from django.contrib import admin
from .models import Recipe, RecipeIngredient, RecipeTag, Ingredients, Tags


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit')
    search_fields = ('name',)


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'created_at')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline, RecipeTagInline]