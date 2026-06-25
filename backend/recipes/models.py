from django.db import models
from users.models import User


class Ingredients(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингредиента'
    )
    unit = models.CharField(
        max_length=100,
        verbose_name='Единица измерения'
    )

    def __str__(self):
        return self.name


class Tags(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг тега'
    )

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента',
        help_text='Введите количество ингредиента'
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return f'{self.amount} {self.ingredient.unit} {self.ingredient.name} в {self.recipe.name}'


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )

    text = models.TextField(
        verbose_name='Описание рецепта'
    )

    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Введите время приготовления в минутах'
    )

    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение рецепта'
    )

    ingredients = models.ManyToManyField(
        Ingredients,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Рецепт'
    )

    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        related_name='tag_recipes',
        verbose_name='Тег'
    )

    class Meta:
        unique_together = ('recipe', 'tag')
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return f'Тег {self.tag.name} рецепта {self.recipe.name}'
