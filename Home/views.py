from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse,HttpResponseForbidden
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
from django.core.cache import cache
import uuid
from django.utils import timezone
from Home.email_sender import send_email_forgot_password
from datetime import date,timedelta,datetime
from django.contrib.auth.decorators import login_required  
import jwt
from restau_panel.models import restaurantMenuCategory, restaurantMenuItems, restaurantTable,restaurantOrderReview



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
        
        if not User.objects.filter(username=email).exists():
            cache.set(attempts_key, attempts + 1, RATE_LIMIT_TIMEOUT)
            messages.error(request, "Email address does not exist.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        user = authenticate(username=email, password=password)
        
        if user is None:
            cache.set(attempts_key, attempts + 1, RATE_LIMIT_TIMEOUT)
            messages.error(request, "Incorrect password.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        restaurant_subscription = RestaurantSubscription.objects.filter(restaurant=user).first()
        if restaurant_subscription is None:
            messages.error(request, "No subscription associated with this account.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        if not restaurant_subscription.is_paid:
            messages.error(request, "Your subscription is not paid yet.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})

        if restaurant_subscription.expiration_date and restaurant_subscription.expiration_date < date.today():
            messages.error(request, "Your subscription has expired. Please renew your subscription to continue.")
            return render(request, 'Home/restaurant-login-page.html', {"email": email})
        
        cache.delete(attempts_key)
        
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


@login_required(login_url="restaurant-login")
def restaurant_Logout(request):
    logout(request)
    return redirect("restaurant-login")


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
            
            restaurant_email = restaurant_obj.email
            
            send_email_forgot_password(restaurant_email, token)
            
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



# ------------------ Function views for the Showing the Menu of the restaurant  -----------------------------

def show_menu(request, restaurant_id):
    # Get the QR data from the URL
    qr_data = request.GET.get('qr_data')
    
    if not qr_data:
        return HttpResponseForbidden("QR data is missing or invalid.")
    
    check_qr_data = restaurantTable.objects.filter(qr_data=qr_data)  
    if not check_qr_data:
        return HttpResponseForbidden("<h4>Invalid QR Code / Table's QR Code is Deleted. please try to scan new QR code.</h4>")
    
    try:
        # Decode the QR data using the secret key
        decoded_data = jwt.decode(qr_data, settings.SECRET_KEY, algorithms=['HS256'])
        table_number = decoded_data.get('table_number')
        decoded_restaurant_id = decoded_data.get('restaurant_id')

        # Validate restaurant ID
        if int(decoded_restaurant_id) != restaurant_id:
            return HttpResponseForbidden("Invalid restaurant information.")
        
        # Get the restaurant and associated categories
        restaurant = get_object_or_404(RestaurantSubscription, id=restaurant_id)
        categories = restaurant.categories.filter(is_active=True)
        
        # Get all menu items associated with the restaurant
        menu_items = restaurantMenuItems.objects.filter(category__restaurant=restaurant, availability=True)
    
    except jwt.ExpiredSignatureError:
        return HttpResponseForbidden("QR code has expired.")
    except jwt.InvalidTokenError:
        return HttpResponseForbidden("Invalid QR data.")
    except Exception as e:
        return HttpResponseForbidden(f"An error occurred: {str(e)}")

    # Prepare context data for rendering
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'menu_items': menu_items,
        'table_number': table_number,
        'restaurant_id' : restaurant_id
    }
    return render(request, 'Home/show_menu.html', context)






# ------------------ Here Views are ended for the Showing the Menu of the restaurant  -----------------------------


# ------------------ Function views for the Processing the checkout functionality  -----------------------------

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from restau_panel.models import restaurantMenuItems, restaurantOrder, restaurantOrderItem
import json


def checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            restaurant_id = data.get('restaurant_id')
            tableNumber = data.get('table_Number')

            try:
                restaurant_id = int(restaurant_id)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid restaurant ID'}, status=400)

            
            try:
                restaurant = RestaurantSubscription.objects.get(id=restaurant_id)  
                
            except RestaurantSubscription.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Restaurant not found'}, status=404)

            if not items:
                return JsonResponse({'success': False, 'error': 'No items provided'}, status=400)
            
            try:
                tableNumber = int(tableNumber)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid Table Number'}, status=400)

            
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key

            total_price = 0
            order_items = [] 

            for item in items:
                menu_item_id = item.get('menu_item_id')
                quantity = item.get('quantity', 0)
                price = item.get('price', 0.0)

                try:
                    menu_item = restaurantMenuItems.objects.get(id=menu_item_id)
                except restaurantMenuItems.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Invalid menu item ID: {menu_item_id}'}, status=400)

                total_price += quantity * price

                
                menu_item.order_times += quantity
                menu_item.save()

                
                order_items.append({
                    'menu_item': menu_item,
                    'quantity': quantity,
                    'price': price
                })

           
            order = restaurantOrder.objects.create(
                restaurant=restaurant,
                table_Number=tableNumber,
                session_id=session_id,
                total_price=total_price,
            )

            # Save the items associated with this order
            for order_item in order_items:
                restaurantOrderItem.objects.create(
                    order=order,
                    menu_item=order_item['menu_item'],
                    quantity=order_item['quantity'],
                    price=order_item['price']
                )

            return JsonResponse({'success': True, 'order_id': order.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)






def order_history(request):
    # Get the session ID from the current session
    session_id = request.session.session_key
    if not session_id:
        return HttpResponse('<h4>No session found. Please place an order first.</h4>')

    # Retrieve orders for this session
    orders = restaurantOrder.objects.filter(session_id=session_id).order_by('-created_at')

    # For each order, check if there is an associated review
    for order in orders:
        order.review = restaurantOrderReview.objects.filter(order=order).first()
        # Create a list of stars based on the rating
        if order.review:
            order.stars = ['filled'] * order.review.rating + ['empty'] * (5 - order.review.rating)
        else:
            order.stars = []

    # Pass orders (with reviews, if any) to the template
    return render(request, 'Home/user_order_history.html', {'orders': orders})






# ------------------ Here Views are ended for the Processing the checkout functionality  -----------------------------


