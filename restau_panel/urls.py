from django.urls import path
from restau_panel.views import *

urlpatterns = [
    path('', restauDashboard, name='restau-dashboard'),
    path('menu/',restauMenu, name='restau-menu'),
    path('orders/',restauOrders,name='restau-orders'),
    path('customer-reviews/',restauCustomerReviews,name='restau-customer-reviews'),
    path('tables/', restauTables.as_view(), name='restau-tables'),
    
    path('add-category/',restauAddCategory,name='restau-add-category'),
    path('add-menu-item/',restauAddMenuItem,name='restau-add-menu-item'),
    path('fetch-menu-items/', fetchMenuItemsByCategory, name='fetch_menu_items_by_category'),
    path('generate-image/<int:table_id>/', generate_pdf_from_html, name='generate_image_card'),
    path('delete_qr_code/<int:table_id>/', delete_qr_code, name='delete_qr_code'),
    
    
]