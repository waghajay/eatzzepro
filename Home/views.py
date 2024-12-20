from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.models import User
from Home.models import RestaurantSubscription,RestaurantForgotPassword
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
import uuid
from django.utils import timezone
from Home.email_sender import send_email_forgot_password
from datetime import date,timedelta


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


# ------------------ Function views for the Forgot Password  -----------------------------

def restaurantForgotPassword(request):
    try:
        if request.method == 'POST':
            email = request.POST.get('email')
        
            if not User.objects.filter(username=email).exists():
                messages.error(request, 'Email address does not exist.')
                return render(request, 'Home/forgot-password.html')
            
            token = str(uuid.uuid4())            
            
            restaurant_obj = User.objects.filter(username=email).first()
            restaurant_subscription_obj = RestaurantSubscription.objects.get(restaurant=restaurant_obj)
            restaurant_forgot_password_obj = RestaurantForgotPassword.objects.create(restaurant_user=restaurant_subscription_obj,password_reset_token=token)
            restaurant_forgot_password_obj.save()
            
            # Send email with the token
            send_email_forgot_password(email, token)
            
            messages.success(request, 'An email has been sent to your registered email address with instructions to reset your password.')
            return redirect('restaurant-login')
        
        
    except Exception as e:
        print(e)
    return render(request, 'Home/forgot-password.html')


def restaurantChangePassword(request, token):
    context = {}
    try:
        restaurant_forgot_password_obj = RestaurantForgotPassword.objects.filter(password_reset_token=token).first()
        
        if not restaurant_forgot_password_obj:
            messages.error(request, 'Invalid or expired password reset token.')
            return redirect("restaurant-login")
        
        context = {'restaurant_id': restaurant_forgot_password_obj.restaurant_user.restaurant.id}
        
        if request.method == 'POST':
            restaurant_id = request.POST.get('restaurant_id')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if not restaurant_id:
                messages.error(request, 'No Restaurant ID found.')
                return redirect(f'/restaurant/restaurant-change-password/{token}/')
            
            restaurant_user = User.objects.get(id=restaurant_id)
            restaurant_user.set_password(password)
            restaurant_user.save()
            
            messages.success(request, 'Password reset successfully.')
            return redirect("restaurant-login")
    
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, 'An error occurred. Please try again later.')
    
    return render(request, 'Home/change-password.html', context)





# ----------------- Here Views are ended for the Login  Restaurant -----------------------------
