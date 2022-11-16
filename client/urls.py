from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout),
    path('profile', views.profile, name='profile'),
    path('password', views.password, name='password'),
    path('restaurant_list', views.restaurant_list, name='restaurant_list'),
    path('payment', views.payment, name='payment')
]
