from django.contrib import admin
from restau_panel.models import restaurantMenuCategory,restaurantMenuItems

# Register your models here.

@admin.register(restaurantMenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    search_fields = ('name', 'description')  # Added 'restaurant_name'
    
@admin.register(restaurantMenuItems)
class MenuItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'availability','order_times')
    search_fields = ('name', 'price', 'date_of_add', 'order_times','availability')

