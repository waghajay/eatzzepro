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
    
    

