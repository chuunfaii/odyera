from django.db import models


class Customer(models.Model):
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    email_address = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=254)
