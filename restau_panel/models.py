from django.db import models
from Home.models import RestaurantSubscription

# Create your models here.

class restaurantMenuCategory(models.Model):
    restaurant = models.ForeignKey(RestaurantSubscription, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Restaurant Name:- {self.restaurant.restaurant_name} ||  ---- Category Name:- {self.name}"
    
    
class restaurantMenuItems(models.Model):
    restaurant = models.ForeignKey(RestaurantSubscription, on_delete=models.CASCADE)
    category = models.ForeignKey(restaurantMenuCategory, on_delete=models.CASCADE, related_name="Menu_Items")
    name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=20, blank=True)
    item_taste = models.CharField(max_length=20)
    price = models.IntegerField()
    availability = models.BooleanField(default=True)
    date_of_add = models.DateTimeField(auto_now_add=True)
    order_times = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Name:- {self.name} --- Price:- {self.price} Restaurant Name:- {self.category.restaurant.restaurant_name}" 
     
    
    

