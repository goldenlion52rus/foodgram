from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipesIngredients,
    ShoppingCart,
    Tag
)


class IngredientInRecipeInline(admin.TabularInline):

    model = RecipesIngredients
    extra = 1
    min_num = 1
    max_num = 50


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Модель тегов в админке."""

    llist_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Модель ингредиентов в админке."""

    list_display = ('name', 'measurement_unit')
    list_filter = ("name",)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Модель рецептов в админке."""

    inlines = [IngredientInRecipeInline]
    list_display = ('id', 'name', 'author')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author', 'tags')

    def in_favorite(self, obj):
        count = obj.in_favorite.all().count()
        return count

    in_favorite.short_description = "Количество добавлений в избранное."


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Модель избранного в админке."""

    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Модель списка покупок в админке."""

    list_display = ('id', 'user', 'recipe')


@admin.register(RecipesIngredients)
class RecipeIngredientAdmin(admin.ModelAdmin):

    list_display = ('recipe', 'ingredient', 'amount')
