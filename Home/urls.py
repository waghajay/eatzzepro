from django.urls import path
from Home.views import *

urlpatterns = [
    path('',index,name='index'),
    path('subscribe-subscription/',subscribeSubscription,name='subscribe-subscription'),
    path('restaurant/login/',restaurant_Login,name="restaurant-login")
]