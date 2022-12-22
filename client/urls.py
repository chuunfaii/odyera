from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
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
    path('order-history', views.order_history, name='order_history'),
    path('malaysia-food-trend', views.malaysia_food_trend,
         name='malaysia_food_trend'),
    path('food-trend', views.food_trend, name='food_trend'),
    path('dashboard', views.dashboard, name='dashboard')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'client.views.error_404'
