from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def short_link_redirect(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
