# Generated by Django 4.1.3 on 2022-11-23 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='image_url',
            field=models.CharField(default='food.png', max_length=254),
            preserve_default=False,
        ),
    ]
