from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .const import MAX_LEN_EMAIL, MAX_LEN_PASSWORD, MAX_LEN_USERNAME


class User(AbstractUser):
    """Создание модели пользователя."""

    email = models.EmailField(
        max_length=MAX_LEN_EMAIL,
        unique=True,
        verbose_name='Адрес электронной почты',
    )
    username = models.CharField(
        max_length=MAX_LEN_USERNAME,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Недопустимый символ в имени пользователя'
        )],
        verbose_name='Уникальный юзернейм',
    )
    first_name = models.CharField(
        max_length=MAX_LEN_USERNAME,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LEN_USERNAME,
        verbose_name='Фамилия',
    )
    password = models.CharField(
        max_length=MAX_LEN_PASSWORD,
        verbose_name='Пароль',
    )
    avatar = models.ImageField(
        upload_to='user_images',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_author',
        verbose_name="Автор",
        default=None
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow',
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
