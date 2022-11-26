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
    path('restaurant/<int:id>', views.restaurant, name='restaurant'),
    path('restaurant/<int:id>/menu', views.menu, name='menu'),
    path('restaurant/<int:id>/order', views.order, name='order'),
    path('restaurant/<int:id>/payment', views.payment, name='payment'),
    # path('foodTrend_particular', views.foodTrend_particular,
    #      name='foodTrend_particular'),
    # path('foodTrend_whole', views.foodTrend_whole, name='foodTrend_whole'),
    path('order_history', views.order_history, name='order_history'),
    # path('report_whole', views.report_whole, name='report_whole'),
    # path('report_particular', views.report_particular, name='report_particular'),
    path('malaysia-food-trend', views.malaysia_food_trend,
         name='malaysia_food_trend'),
    path('food-trend', views.food_trend, name='food_trend')
]
