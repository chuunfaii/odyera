from django.db import models
from django.contrib.gis.db import models
from django.db.models import Count

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
    location_lon = models.FloatField()
    location_lat = models.FloatField()
    location = models.PointField()
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


class MenuItem(models.Model):
    name = models.CharField(max_length=254)
    description = models.CharField(max_length=254)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image_url = models.ImageField(null=True,blank=True,upload_to="",max_length=254)
    # image_url = models.CharField(max_length=254)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True)


class Order(models.Model):
    date_time = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=6, decimal_places=2)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    subtotal_price = models.DecimalField(max_digits=6, decimal_places=2)


class Payment(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    date_time = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)


class SentimentAnalysis(models.Model):
    polarity_score = models.IntegerField()
    compound_score = models.IntegerField()
    super_score = models.IntegerField()
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
