from django.core.mail import send_mail
from django.conf import settings



def send_email_forgot_password(email, token):
    subject = "Password Reset Request"
    message = f"To reset your password, visit the following link: https://eatzzepro.com/restaurant/restaurant-change-password/{token}/"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    
    return True