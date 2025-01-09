from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import restaurantOrder

@receiver(post_save, sender=restaurantOrder)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        restaurant_id = instance.restaurant.id
        table_number = instance.table_Number
        order_id = instance.id
        total_price = instance.total_price

        message = f'New order received! Table {table_number}, Order ID: {order_id}, Total: {total_price}'

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'restaurant_{restaurant_id}_notifications',
            {
                'type': 'send_notification',
                'message': message,
            }
        )
