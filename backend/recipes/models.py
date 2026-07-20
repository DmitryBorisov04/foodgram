from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

MIN_COOKING_TIME = 1
MIN_PRODUCT_AMOUNT = 1


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=(
                    'Ник может содержать только буквы, цифры '
                    'и символы @/./+/-/_.'
                ),
            )
        ],
        verbose_name='Ник',
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта',
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='avatar/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Product(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название продукта',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('name', 'measurement_unit')
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_product_measurement_unit',
            ),
        )
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='идентификатор',
        max_length=32,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveIntegerField(
        validators=(MinValueValidator(MIN_COOKING_TIME),),
        verbose_name='Время приготовления',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение рецепта',
    )
    products = models.ManyToManyField(
        Product,
        through='RecipeProduct',
        verbose_name='Продукты',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        ordering = ('name',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeProduct(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
    )
    amount = models.PositiveIntegerField(
        validators=(MinValueValidator(MIN_PRODUCT_AMOUNT),),
        verbose_name='Количество продукта',
    )

    class Meta:
        ordering = ('recipe', 'product')
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'product'),
                name='unique_recipe_product',
            ),
        )
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецепта'
        default_related_name = 'recipe_products'

    def __str__(self):
        return (
            f'{self.amount} {self.product.measurement_unit} '
            f'{self.product.name} в {self.recipe.name}'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('user__username', 'author__username')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_user_recipe',
            ),
        )

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class Favorite(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
