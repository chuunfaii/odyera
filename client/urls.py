from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout),
    path('profile', views.profile, name='profile'),
    path('password', views.password, name='password'),
    path('restaurants', views.restaurants, name='restaurants'),
    path('payment', views.payment, name='payment'),
    path('restaurant_detail', views.restaurant_detail, name='restaurant_detail'),
    path('foodTrend_particular', views.foodTrend_particular,
         name='foodTrend_particular'),
    path('foodTrend_whole', views.foodTrend_whole, name='foodTrend_whole'),

]
