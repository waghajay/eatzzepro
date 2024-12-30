from django.db import models
from Home.models import RestaurantSubscription
import qrcode
import jwt
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
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
     
     
class restaurantTable(models.Model):
    restaurant = models.ForeignKey(RestaurantSubscription, on_delete=models.CASCADE)  # Reference to the restaurant
    number = models.IntegerField()
    qr_code_url = models.URLField(blank=True, null=True)
    qr_code_image = models.ImageField(upload_to='QR_codes/', blank=True, null=True)
    qr_data = models.CharField(max_length=255, blank=True, null=True,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_qr_code(self):
        # Embed data about the table and restaurant in the QR code
        table_data = {
            'table_number': self.number,
            'restaurant_id': self.restaurant.id  # Include restaurant ID to differentiate between restaurants
        }

        # Encode the data into a JWT
        token = jwt.encode(table_data, settings.SECRET_KEY, algorithm='HS256')

        # Generate QR code with the encoded token
        external_url = f"http://127.0.0.1:8000/{self.restaurant.id}/menu/"  # Unique URL for each restaurant
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(external_url + f"?qr_data={token}")
        qr.make(fit=True)

        # Create a BytesIO buffer to save the image
        buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buffer, format='PNG')

        # Save the QR code image in the model
        self.qr_code_image.save(f"{self.restaurant.id}_table_{self.number}.png", ContentFile(buffer.getvalue()))
        self.qr_code_url = external_url + f"?qr_data={token}"
        self.qr_data = token

    def save(self, *args, **kwargs):
        # Check if the model is being saved for the first time or if some other condition applies
        if not self.qr_code_image:
            self.generate_qr_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Table {self.number} - {self.restaurant.restaurant_name}"
    
    
    
class restaurantOrder(models.Model):
    order_status = (
        ('Pending','Pending'),
        ('Accepted','Accepted'),
        ('Rejected', "Rejected")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    order_status = models.CharField(max_length=30,choices=order_status,default="Pending")
    
    def __str__(self):
        return f"Order ID :- {self.id} --- Amount :- {self.total_price}"
    
    
    
class restaurantOrderItem(models.Model):
    order = models.ForeignKey(restaurantOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(restaurantMenuItems, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Order ID :- {self.id} ---- Menu Item :- {self.menu_item.name} ---- Quantity :- {self.quantity} ---- Price :- {self.price}"
    
    
    

