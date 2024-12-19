from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.models import User
from Home.models import RestaurantSubscription
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading
from django.contrib.auth import authenticate,login,logout
from django.middleware.csrf import get_token
from datetime import datetime, date
from django.core.cache import cache

from django.utils import timezone


# Create your views here.

def index(request):
    return render(request, 'Home/index.html')


# ------------------ Function Views for Registering New Restaurant --------------------------------

def subscribeSubscription(request):
    if request.method == 'POST':
        restaurant_name = request.POST.get("restaurant_name")
        owner_name = request.POST.get("owner_name")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        password = request.POST.get("password")
        plan = request.POST.get("selected_plan")
        price = request.POST.get("selected_price")
        
        if User.objects.filter(username=email).exists():
            messages.success(request, "Email already taken")
            return render(request, 'Home/index.html', {"restaurant_name": restaurant_name, "email": email})

        user = User.objects.create_user(username=email, password=password, email=email)

        restaurant = RestaurantSubscription.objects.create(
            restaurant=user,
            restaurant_name=restaurant_name,
            owner_name=owner_name,
            phone_number=phone_number,
            plan=plan,
            price=price
        )
        restaurant.save()
        
        restaurant_email=email

        send_email_in_background(restaurant_email,restaurant_name, owner_name, phone_number, plan, price)

        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False})

def send_mail_subscribe_subscription(restaurant_email,restaurant_name, owner_name, phone_number, plan, price):
    email_recipients = ['awagh3120@gmail.com']
    subject = 'EatZzePro :- New Restaurant Registered....'
    html_content = render_to_string(
        'Home/admin_email_nofication.html', 
        {
            'restaurant_email': restaurant_email,
            'restaurant_name': restaurant_name,
            'owner_name': owner_name,
            'phone_number': phone_number,
            'plan': plan,
            'price': price
        }
    )
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, email_recipients)
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        print(f"Email sent successfully to {', '.join(email_recipients)}")
    except Exception as e:
        print(f"Error while sending email: {e}")

def send_email_in_background(restaurant_email,restaurant_name, owner_name, phone_number, plan, price):
    thread = threading.Thread(
        target=send_mail_subscribe_subscription,
        args=(restaurant_email,restaurant_name, owner_name, phone_number, plan, price)
    )
    thread.start()
    
# ----------------- Here Views are ended for the  Restaurant Registration -----------------------------



# ------------------ Function Views for Login Restaurant -----------------------------------------------

LOGIN_RATE_LIMIT = 5
RATE_LIMIT_TIMEOUT = 60 * 15

from datetime import date

def restaurant_Login(request):
    if request.method == "POST":
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        
        # --- Security: Rate Limiting ---
        client_ip = get_client_ip(request)
        attempts_key = f"login_attempts_{client_ip}"
        block_key = f"block_{client_ip}"
        
        if cache.get(block_key):
            messages.error(request, "Too many failed login attempts. Please try again later.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        attempts = cache.get(attempts_key, 0)
        if attempts >= LOGIN_RATE_LIMIT:
            cache.set(block_key, True, RATE_LIMIT_TIMEOUT)
            cache.delete(attempts_key)
            messages.error(request, "Too many failed login attempts. Please try again later.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        # Check if email exists
        if not User.objects.filter(username=email).exists():
            cache.set(attempts_key, attempts + 1, RATE_LIMIT_TIMEOUT)
            messages.error(request, "Email address does not exist.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if user is None:
            cache.set(attempts_key, attempts + 1, RATE_LIMIT_TIMEOUT)
            messages.error(request, "Incorrect password.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        # Check if the subscription is valid
        restaurant_subscription = RestaurantSubscription.objects.filter(restaurant=user).first()
        if restaurant_subscription is None:
            messages.error(request, "No subscription associated with this account.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        if not restaurant_subscription.is_paid:
            messages.error(request, "Your subscription is not paid yet.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        # Compare expiration_date with the current date
        if restaurant_subscription.expiration_date and restaurant_subscription.expiration_date < date.today():
            messages.error(request, "Your subscription has expired. Please renew your subscription to continue.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        # Clear rate-limiting counters upon successful login
        cache.delete(attempts_key)
        
        # Log in the user
        login(request, user)
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('restau-dashboard')

    return render(request, 'Home/restaurant-login-page.html')

def get_client_ip(request):
    """Retrieve the client's IP address from the request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ----------------- Here Views are ended for the Login  Restaurant -----------------------------
