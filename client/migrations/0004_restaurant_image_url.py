# Generated by Django 4.1.3 on 2022-11-20 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0003_cuisine_restaurantowner_review_restaurant_menuitem_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='image_url',
            field=models.CharField(default='restaurant.png', max_length=254),
            preserve_default=False,
        ),
    ]
