from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User  # 

class RestaurantSubscription(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    plan = models.CharField(max_length=50)  # Plan options: '1 Month', '2 Months', '3 Months'
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Set expiration date based on selected plan
        if self.plan == '1 Month':
            self.expiration_date = timezone.now() + timedelta(days=30)
        elif self.plan == '2 Months':
            self.expiration_date = timezone.now() + timedelta(days=60)
        elif self.plan == '3 Months':
            self.expiration_date = timezone.now() + timedelta(days=90)

        super(RestaurantSubscription, self).save(*args, **kwargs)

    def __str__(self):
        return f"Subscription for {self.restaurant_name} - {self.plan} - Paid :- {self.is_paid}"
    
    
class RestaurantForgotPassword(models.Model):
    restaurant_user = models.ForeignKey(RestaurantSubscription, on_delete=models.CASCADE)
    password_reset_token = models.CharField(max_length=100, unique=True)
    created_at = models.DateField(auto_now_add=True)
    password_reset_expiration = models.DateTimeField()

    def save(self, *args, **kwargs):
        # Set expiration date to 24 hours from now if not already set
        if not self.password_reset_expiration:
            self.password_reset_expiration = timezone.now() + timedelta(days=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Restaurant :- {self.restaurant_user.restaurant_name} --- Created at :- {self.created_at}"
    
