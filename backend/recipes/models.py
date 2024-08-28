from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.urls import reverse

from users.models import User

from .consts import (
    LEN_COLOR,
    LEN_INGREDIENT_MEASUREMENT_UNIT,
    LEN_INGREDIENT_NAME,
    LEN_RECIPE_NAME,
    LEN_TAG_NAME,
    LEN_TAG_SLUG,
    LIMIT_VALUE,
    MAX_COOKING_TIME,
    MIN_COOKING_TIME
)


class Tag(models.Model):
    """ Модель Тэг."""
    name = models.CharField(
        'Название Тэга',
        max_length=LEN_TAG_NAME,
        unique=True,
        help_text='Название Тэга',
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=LEN_COLOR,
        unique=True,
        db_index=False,
    )
    slug = models.SlugField(
        max_length=LEN_TAG_SLUG,
        unique=True,
        verbose_name='Slug',
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):

    name = models.CharField(
        'Название ингредиента',
        max_length=LEN_INGREDIENT_NAME,
        unique=True,
        help_text='Название ингредиента',
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=LEN_INGREDIENT_MEASUREMENT_UNIT,
        help_text='Единица измерения',
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепты."""

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор публикации',
    )
    name = models.CharField(
        max_length=LEN_RECIPE_NAME,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipe_images',
        verbose_name='Картинка рецепта',
    )
    text = models.TextField(
        'Описание рецепта',
        help_text='Описание рецепта.',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipesIngredients',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
        blank=True,
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в минутах',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ],
        help_text='Время приготовления в минутах',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def clean(self):
        super().clean()
        if not self.ingredients.exists():
            raise ValidationError('Рецепт должен содержать \
                                  хотя бы один ингредиент!')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'pk': self.pk})


class ShoppingCart(models.Model):
    """Список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart',
            )
        ]

    def __str__(self):
        return (
            'Рецепт {self.recipe} в списке покупок у {self.user}'
        )


class Favorite(models.Model):
    """Избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт',
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('-pub_date',)
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class RecipesIngredients(models.Model):
    """Создание модели связанных ингредиентов в рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(
            limit_value=LIMIT_VALUE,
            message='Минимальное количество 1!'),
        ),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'Количество ингредиента'

    def __str__(self):
        return (
            f'''{self.ingredient.name}
            ({self.ingredient.measurement_unit}) - {self.amount}'''
        )
