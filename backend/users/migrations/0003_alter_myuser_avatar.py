# Generated by Django 3.2.3 on 2024-07-19 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_myuser_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='avatar',
            field=models.ImageField(null=True, upload_to='avatars', verbose_name='Аватар'),
        ),
    ]
