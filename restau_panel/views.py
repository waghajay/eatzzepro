from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
import os
import base64

from Home.models import RestaurantSubscription
from .models import (
    restaurantMenuCategory, 
    restaurantMenuItems, 
    restaurantTable,
    restaurantOrder, 
    restaurantOrderItem,
    restaurantOrderReview
)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, F


def get_restaurant_name(request):
    restaurant = request.user
    restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
    return restaurant_obj.restaurant_name


# --- Dashboard View ---
@login_required(login_url="restaurant-login")
def restauDashboard(request):
    restaurant_name = get_restaurant_name(request=request)
    """Render the restaurant dashboard with relevant metrics and popular food data."""
    try:
        restaurant_logged_in_user = request.user
        restaurant = RestaurantSubscription.objects.get(restaurant=restaurant_logged_in_user)

        # Calculate dashboard metrics
        total_income = restaurantOrder.objects.filter(
            restaurant=restaurant, order_status="Accepted"
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        total_orders = restaurantOrder.objects.filter(restaurant=restaurant).count()
        total_order_accepted = restaurantOrder.objects.filter(restaurant=restaurant, order_status="Accepted").count()
        total_order_rejected = restaurantOrder.objects.filter(restaurant=restaurant, order_status="Rejected").count()
        total_order_pending = restaurantOrder.objects.filter(restaurant=restaurant, order_status="Pending").count()

        # Get popular food items (top 3 ordered)
        popular_food = (
            restaurantOrderItem.objects.filter(order__restaurant=restaurant)
            .values(item_name=F('menu_item__name'))
            .annotate(order_count=Count('menu_item'))
            .order_by('-order_count')
        )
        popular_food_names = [item['item_name'] for item in popular_food]
        popular_food_counts = [item['order_count'] for item in popular_food]

        context = {
            "restaurant_name": restaurant_name,
            "restaurant_id": restaurant.id,
            "total_income": total_income,
            "total_orders": total_orders,
            "total_order_accepted": total_order_accepted,
            "total_order_rejected": total_order_rejected,
            "total_order_pending": total_order_pending,
            "popular_food_names": popular_food_names,
            "popular_food_counts": popular_food_counts,
        }
        return render(request, "restau_panel/dashboard.html", context)

    except RestaurantSubscription.DoesNotExist:
        return render(request, "restau_panel/dashboard.html", {"error": "Restaurant data not found."})


# --- Menu Views ---
@login_required(login_url="restaurant-login")
def restauMenu(request):
    restaurant_name = get_restaurant_name(request=request)
    """Render the restaurant menu page."""
    try:
        restaurant = request.user
        categories = restaurantMenuCategory.objects.filter(restaurant__restaurant=restaurant)
        menu_items = restaurantMenuItems.objects.filter(category__in=categories)
    except Exception as e:
        categories = []
        menu_items = []
        print(f"Error fetching menu: {str(e)}")

    context = {"categories": categories, "menu_items": menu_items ,  "restaurant_name": restaurant_name}
    return render(request, "restau_panel/menu.html", context)


@login_required(login_url="restaurant-login")
def restauAddCategory(request):
    """Add a new menu category."""
    if request.method == "POST":
        try:
            restaurant = request.user
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            category_name = request.POST.get("category_name")
            category_description = request.POST.get("category_description")

            # Save new category
            restaurantMenuCategory.objects.create(
                restaurant=restaurant_obj,
                name=category_name,
                description=category_description,
            )
            return JsonResponse({"success": True, "message": "Category added successfully. Reload the page to see it."})
        except Exception as e:
            print(f"Error adding category: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


@login_required(login_url="restaurant-login")
def restauAddMenuItem(request):
    """Add a new menu item."""
    if request.method == "POST":
        try:
            restaurant = request.user
            item_type = request.POST.get("item_type")
            item_name = request.POST.get("item_name")
            item_taste = request.POST.get("item_taste")
            item_category = request.POST.get("item_category")
            item_price = request.POST.get("item_price")

            # Validate input fields
            if not all([item_type, item_name, item_taste, item_category, item_price]):
                return JsonResponse({"success": False, "message": "All fields are required."}, status=400)
            
            if not item_price.isdigit() or float(item_price) <= 0:
                return JsonResponse({"success": False, "message": "Invalid price value."}, status=400)

            # Get restaurant and category
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            restaurant_category = restaurantMenuCategory.objects.get(
                restaurant=restaurant_obj, name=item_category
            )

            # Save new menu item
            restaurantMenuItems.objects.create(
                restaurant=restaurant_obj,
                category=restaurant_category,
                name=item_name,
                item_type=item_type,
                item_taste=item_taste,
                price=float(item_price),
            )
            return JsonResponse({"success": True, "message": "Menu item added successfully!"})

        except ObjectDoesNotExist as e:
            logger.error(f"Object not found: {str(e)}")
            return JsonResponse({"success": False, "message": "Invalid restaurant or category."}, status=404)

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({"success": False, "message": "Invalid input data."}, status=400)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({"success": False, "message": "An unexpected error occurred. Please try again later."}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)


@login_required(login_url="restaurant-login")
def fetchMenuItemsByCategory(request):
    """Fetch menu items for a specific category."""
    if request.method == "GET":
        category_id = request.GET.get("category_id")
        if not category_id:
            return JsonResponse({"success": False, "error": "Category ID is required."}, status=400)

        try:
            category = restaurantMenuCategory.objects.get(id=category_id)
            menu_items = restaurantMenuItems.objects.filter(category=category)
            items_data = list(menu_items.values("name", "price", "item_type", "item_taste", "category__name"))
            return JsonResponse({"success": True, "menu_items": items_data})
        except restaurantMenuCategory.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found."})

    return JsonResponse({"success": False, "error": "Invalid request method."})



@csrf_exempt  # Temporarily exempt CSRF for the DELETE request, but ideally should use proper CSRF handling
@login_required(login_url="restaurant-login")
def delete_menu_item(request, item_id):
    if request.method == 'DELETE':
        try:
            # Fetch the menu item by ID
            menu_item = get_object_or_404(restaurantMenuItems, id=item_id)

            # Delete the menu item
            menu_item.delete()

            # Return success response
            return JsonResponse({'success': True, 'message': 'Menu item deleted successfully!'})
        except MenuItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Menu item not found!'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required(login_url="restaurant-login")
def toggle_menu_item_availability(request, item_id):
    """Toggle the availability of a menu item."""
    if request.method == "POST":
        try:
            restaurant = request.user
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            item = restaurantMenuItems.objects.get(id=item_id, restaurant=restaurant_obj)
            item.availability = not item.availability  # Toggle the availability
            item.save()

            return JsonResponse({"success": True, "is_available": item.availability})
        except restaurantMenuItems.DoesNotExist:
            return JsonResponse({"success": False, "message": "Menu item not found!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


# --- Orders Views ---
@login_required(login_url="restaurant-login")
def restauOrders(request):
    restaurant_name = get_restaurant_name(request=request)
    """Render the restaurant orders page."""
    try:
        user = request.user
        restaurant_order = restaurantOrder.objects.filter(restaurant__restaurant=user).order_by("-created_at")
        context = {'restaurant_order': restaurant_order, "restaurant_name": restaurant_name}
        return render(request, "restau_panel/orders.html", context)
    except restaurantOrder.DoesNotExist:
        print("No orders found.")
        return render(request, "restau_panel/orders.html")


@login_required(login_url="restaurant-login")
def fetch_order_details(request, order_id):
    """Fetch details of a specific order."""
    order = get_object_or_404(restaurantOrder, id=order_id)
    items = order.items.all()

    order_data = {
        "id": order.id,
        "table_number": order.table_Number,
        "created_at": order.created_at.strftime("%B %d, %Y, %I:%M %p"),
        "total_price": float(order.total_price),
        "status": order.order_status,
        "items": [
            {
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "price": float(item.price),
            }
            for item in items
        ],
    }
    return JsonResponse(order_data)


@csrf_exempt
def accept_order(request, order_id):
    """Accept an order."""
    if request.method == "POST":
        try:
            order_obj = restaurantOrder.objects.filter(id=order_id).first()
            if order_obj:
                order_obj.order_status = "Accepted"
                order_obj.save()
                return JsonResponse({"success": True, "message": "Order Accepted Successfully"})
            return JsonResponse({"success": False, "error": "Order not found."})
        except Exception as e:
            print(f"Error accepting order: {str(e)}")
            return JsonResponse({"success": False, "error": "An error occurred."})

    return JsonResponse({"success": False, "error": "Invalid request method."})


@csrf_exempt
def reject_order(request, order_id):
    """Reject an order."""
    if request.method == "POST":
        try:
            order_obj = restaurantOrder.objects.filter(id=order_id).first()
            if order_obj:
                order_obj.order_status = "Rejected"
                order_obj.save()
                return JsonResponse({"success": True, "message": "Order Rejected Successfully"})
            return JsonResponse({"success": False, "error": "Order not found."})
        except Exception as e:
            print(f"Error rejecting order: {str(e)}")
            return JsonResponse({"success": False, "error": "An error occurred."})

    return JsonResponse({"success": False, "error": "Invalid request method."})


# --- Reviews Views ---
@login_required(login_url="restaurant-login")
def restauCustomerReviews(request):
    """Render the customer reviews page."""
    return render(request, "restau_panel/customer-reviews.html")


def submit_review(request, order_id):
    """Submit a review for an order."""
    if request.method == "POST":
        try:
            order_obj = restaurantOrder.objects.get(id=order_id)
            review_text = request.POST.get('review')
            rating = request.POST.get('rating')

            if not review_text or not rating:
                messages.error(request, 'Review and rating are required.')
                return redirect("order_history")

            restaurantOrderReview.objects.create(
                order=order_obj,
                review_text=review_text,
                rating=rating,
            )
            messages.success(request, 'Review submitted successfully.')
            return redirect("order_history")
        except restaurantOrder.DoesNotExist:
            messages.error(request, 'Order not found.')
            return redirect("order_history")
        except Exception as e:
            print(f"Error submitting review: {str(e)}")
            messages.error(request, 'An error occurred.')
            return redirect("order_history")

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


# --- Tables Management ---
class restauTables(View):
    template_name = 'restau_panel/tables.html'

    def get(self, request, *args, **kwargs):
        restaurant_name = get_restaurant_name(request=request)
        """Render the tables management page."""
        try:
            restaurant = RestaurantSubscription.objects.get(restaurant=request.user)
            tables = restaurantTable.objects.filter(restaurant=restaurant).order_by('number')
            return render(request, self.template_name, {"tables": tables, "restaurant": restaurant,"restaurant_name": restaurant_name})
        except RestaurantSubscription.DoesNotExist:
            return render(request, self.template_name, {"error": "Restaurant not found.","restaurant_name": restaurant_name})

    def post(self, request, *args, **kwargs):
        """Add a new table."""
        table_number = request.POST.get('table_number')
        try:
            restaurant = RestaurantSubscription.objects.get(restaurant=request.user)
            if table_number and not restaurantTable.objects.filter(restaurant=restaurant, number=int(table_number)).exists():
                restaurantTable.objects.create(restaurant=restaurant, number=int(table_number))
                messages.success(request, 'Table created successfully.')
                return redirect("restau-tables")

            messages.error(request, 'Invalid table number or table already exists.')
        except Exception as e:
            print(f"Error adding table: {str(e)}")

        return redirect("restau-tables")


# --- QR Code PDF Generation ---
@login_required(login_url="restaurant-login")
def generate_pdf_from_html(request, table_id):
    """Generate and download a PDF for a table's QR code."""
    try:
        table = get_object_or_404(restaurantTable, id=table_id)
        qr_code_image_path = os.path.join(settings.MEDIA_ROOT, table.qr_code_image.name)
        with open(qr_code_image_path, "rb") as image_file:
            qr_code_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        context = {
            'table_number': table.number,
            'restaurant_name': table.restaurant.restaurant_name,
            'qr_code_image_base64': qr_code_image_base64,
        }
        html = render_to_string('restau_panel/qr_download_template.html', context)
        buffer = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), buffer)

        if not pdf.err:
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="table_{table.number}_qr_code.pdf"'
            return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")

    return HttpResponse("Error generating PDF", status=500)


def delete_qr_code(request, table_id):
    """Delete a table's QR code."""
    try:
        table = get_object_or_404(restaurantTable, id=table_id)
        table.delete()
        return redirect("restau-tables")
    except Exception as e:
        print(f"Error deleting table: {str(e)}")
        return HttpResponse("Error deleting table", status=500)
