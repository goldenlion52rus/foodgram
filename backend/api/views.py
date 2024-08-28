from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitPagination
from api.serializers import (
    CustomUserSerializer,
    FavoriteSerializer,
    GetRecipeSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserAvatarSerializer
)
from recipes.models import Ingredient, Recipe, RecipesIngredients, Tag
from users.models import Subscribe

User = get_user_model()


class UsersViewSet(UserViewSet):
    """ViewSet для модели Пользователя."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(
        methods=['PUT', 'DELETE'],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='me/avatar',
    )
    def avatar(self, request):
        if request.method == 'PUT':
            instance = self.get_instance()
            serializer = UserAvatarSerializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            instance = self.get_instance()
            instance.avatar = None
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        detail=True,
    )
    def subscribe(self, request, id):
        """Метод для управления подписками."""

        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if author == user:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscribeSerializer(author, context={'request': request})
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        is_subscribed = user.follower.filter(author=author).exists()
        if not is_subscribed:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user.follower.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """Метод для подписки."""
        user = request.user
        follows = User.objects.filter(subscribing__user=user)
        page = self.paginate_queryset(follows)
        serializer = SubscribeSerializer(page,
                                         many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='me',
    )
    def me(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов на получение ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов на получение тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in SAFE_METHODS:
            return GetRecipeSerializer
        return RecipeSerializer
    
    def add_to(self, serializer):
        serializer.save(author=self.request.user)

    def delete_from(self, request, *args, **kwargs):
        if self.request.user != self.get_object().author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            is_favorited = user.favourites.filter(recipe=recipe)
            if is_favorited.exists():
                is_favorited.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                data={'errors': 'Этого рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
    
    @action(
        detail=True,
        methods=['GET'],
        url_path='get-link',
    )
    def get_link(self, request, pk):
        get_object_or_404(Recipe, id=pk)
        return Response(
            {'short-link': f'{settings.HOST}/recipes/{pk}'},
            status=status.HTTP_200_OK
        )
    
    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = (
            RecipesIngredients.objects.filter(
                recipe__in_shopping_cart__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        today = timezone.now()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%d-%m-%Y}\n\n'
        )
        shopping_list += '\n'.join([
            f"- {ingredient['ingredient__name']}" # noqa
            f"({ingredient['ingredient__measurement_unit']})"
            f" - {ingredient['quantity']}"
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

