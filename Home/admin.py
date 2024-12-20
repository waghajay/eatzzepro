from django.contrib import admin

from Home.models import RestaurantSubscription,RestaurantForgotPassword

# Register your models here.

admin.site.register(RestaurantSubscription)
admin.site.register(RestaurantForgotPassword)