from django.db import models


class Customer(models.Model):
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    email_address = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=254)


class RestaurantOwner(models.Model):
    email_address = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=254)


class Restaurant(models.Model):
    name = models.CharField(max_length=254)
    description = models.CharField(max_length=254)
    location_lon = models.CharField(max_length=254)
    location_lat = models.CharField(max_length=254)
    operating_hours_start = models.CharField(max_length=254)
    operating_hours_end = models.CharField(max_length=254)
    image_url = models.CharField(max_length=254)
    owner = models.ForeignKey(RestaurantOwner, on_delete=models.CASCADE)


class Review(models.Model):
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    text = models.CharField(max_length=254)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE)


class Cuisine(models.Model):
    name = models.CharField(max_length=254)


class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)


class MenuItem(models.Model):
    name = models.CharField(max_length=254)
    description = models.CharField(max_length=254)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE)
