from django.contrib import admin
from restau_panel.models import restaurantMenuCategory

# Register your models here.

@admin.register(restaurantMenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'is_active')
    search_fields = ('name', 'description')  # Added 'restaurant_name'

