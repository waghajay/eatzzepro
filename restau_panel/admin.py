from django.contrib import admin
from restau_panel.models import restaurantMenuCategory,restaurantMenuItems,restaurantTable

# Register your models here.

@admin.register(restaurantMenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    search_fields = ('name', 'description')  # Added 'restaurant_name'
    
@admin.register(restaurantMenuItems)
class MenuItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'availability','order_times')
    search_fields = ('name', 'price', 'date_of_add', 'order_times','availability')
    
    
@admin.register(restaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('number','restaurant')
    search_fields = ('number', 'qr_code_url')
    

