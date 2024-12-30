from django.urls import path
from Home.views import *

urlpatterns = [
    path('',index,name='index'),
    path('subscribe-subscription/',subscribeSubscription,name='subscribe-subscription'),
    path('restaurant/login/',restaurant_Login,name="restaurant-login"),
    path('restaurant/logout/',restaurant_Logout,name="restaurant-logout"),
    path('restaurant/restaurant-forgot-password/',restaurantForgotPassword,name="restaurant-forgot-password"),
    path('restaurant/restaurant-change-password/<token>/',restaurantChangePassword,name="restaurant-change-password"),
    
    path('<int:restaurant_id>/menu/', show_menu, name='show_menu'),
    path('checkout/',checkout,name='checkout'),
    path('order-history/',order_history,name='order_history')
    
]