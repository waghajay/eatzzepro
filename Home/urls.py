from django.urls import path
from Home.views import *

urlpatterns = [
    path('',index,name='index'),
    path('subscribe-subscription/',subscribeSubscription,name='subscribe-subscription'),
    path('restaurant/login/',restaurant_Login,name="restaurant-login"),
    path('restaurant/restaurant-forgot-password/',restaurantForgotPassword,name="restaurant-forgot-password"),
    path('restaurant/restaurant-change-password/<token>/',restaurantChangePassword,name="restaurant-change-password")
]