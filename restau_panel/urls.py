from django.urls import path
from restau_panel.views import *

urlpatterns = [
    path('', restauDashboard, name='restau-dashboard'),
    path('menu/',restauMenu, name='restau-menu'),
    path('orders/',restauOrders,name='restau-orders'),
    path('customer-reviews/',restauCustomerReviews,name='restau-customer-reviews'),
    path('tables/',restauTables, name='restau-tables')
]