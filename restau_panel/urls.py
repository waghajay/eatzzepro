from django.urls import path
from restau_panel.views import *

urlpatterns = [
    path('', restauDashboard, name='restau-dashboard'),
    # path('menu/',restauMenu, name='restau-menu'),
    # path('order/',restauOrders,name='restau-order'),
    # path('restau-login/',restauLogin, name='restau-login'),
]