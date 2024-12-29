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
from .models import restaurantMenuCategory, restaurantMenuItems, restaurantTable
from django.conf import settings


# View for the restaurant login page
@login_required(login_url="restaurant-login")
def restauLogin(request):
    return render(request, "restau_panel/restau_login.html")


# View for the restaurant dashboard
@login_required(login_url="restaurant-login")
def restauDashboard(request):
    return render(request, "restau_panel/dashboard.html")


# View to display restaurant menu
@login_required(login_url="restaurant-login")
def restauMenu(request):
    restaurant = request.user
    try:
        # Fetch menu categories and items for the restaurant
        categories = restaurantMenuCategory.objects.filter(restaurant__restaurant=restaurant)
        menu_items = restaurantMenuItems.objects.filter(category__in=categories)  # Multiple categories
    except Exception as e:
        categories = []
        menu_items = []
        print(str(e))

    context = {"categories": categories, "menu_items": menu_items}
    return render(request, "restau_panel/menu.html", context)


# View to add a new menu category
@login_required(login_url="restaurant-login")
def restauAddCategory(request):
    if request.method == "POST":
        restaurant = request.user
        try:
            # Get restaurant and category details from POST request
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            category_name = request.POST.get("category_name")
            category_description = request.POST.get("category_description")

            # Save the new category
            restaurantMenuCategory.objects.create(
                restaurant=restaurant_obj,
                name=category_name,
                description=category_description,
            )
            return JsonResponse({
                "success": True,
                "message": "Category added successfully. Reload the page to see the category",
            })
        except Exception as e:
            print(str(e))
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


# View to add a new menu item
@login_required(login_url="restaurant-login")
def restauAddMenuItem(request):
    if request.method == "POST":
        try:
            # Get item details from POST request
            restaurant = request.user
            item_type = request.POST.get("item_type")
            item_name = request.POST.get("item_name")
            item_taste = request.POST.get("item_taste")
            item_category = request.POST.get("item_category")
            item_price = request.POST.get("item_price")

            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            restaurant_category = restaurantMenuCategory.objects.get(
                restaurant=restaurant_obj, name=item_category
            )

            # Save the new menu item
            restaurantMenuItems.objects.create(
                restaurant=restaurant_obj,
                category=restaurant_category,
                name=item_name,
                item_type=item_type,
                item_taste=item_taste,
                price=item_price,
            )

            return JsonResponse({"success": True, "message": "Menu item added successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


# View to fetch menu items by category
@login_required(login_url="restaurant-login")
def fetchMenuItemsByCategory(request):
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


# View for restaurant orders page
@login_required(login_url="restaurant-login")
def restauOrders(request):
    return render(request, "restau_panel/orders.html")


# View for restaurant customer reviews page
@login_required(login_url="restaurant-login")
def restauCustomerReviews(request):
    return render(request, "restau_panel/customer-reviews.html")


# View for restaurant tables management
class restauTables(View):
    template_name = 'restau_panel/tables.html'

    def get(self, request, *args, **kwargs):
        # Fetch the logged-in user's restaurant
        restaurant = RestaurantSubscription.objects.get(restaurant=request.user)
        tables = restaurantTable.objects.filter(restaurant=restaurant)  # Fetch tables for the logged-in restaurant
        return render(request, self.template_name, {"tables": tables, "restaurant": restaurant})

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            table_number = request.POST.get('table_number')

            # Fetch the logged-in user's restaurant
            restaurant = RestaurantSubscription.objects.get(restaurant=request.user)

            if table_number:
                table_number = int(table_number)

                # Check if table already exists for the logged-in restaurant
                if not restaurantTable.objects.filter(restaurant=restaurant, number=table_number).exists():
                    # Create a new table instance for the restaurant
                    table = restaurantTable(restaurant=restaurant, number=table_number)
                    table.save()
                    messages.success(request, 'Table created successfully.')
                    return redirect("restau-tables")

            # Error or table already exists, show error message
            tables = restaurantTable.objects.filter(restaurant=restaurant)
            messages.error(request, 'Invalid request or table number already exists.')
            return render(request, self.template_name, {"tables": tables, "restaurant": restaurant})


# Function to generate a PDF from HTML template
@login_required(login_url="restaurant-login")
def generate_pdf_from_html(request, table_id):
    # Fetch the table object
    table = get_object_or_404(restaurantTable, id=table_id)

    # Get the QR code image file path and convert it to Base64
    qr_code_image_path = os.path.join(settings.MEDIA_ROOT, table.qr_code_image.name)
    with open(qr_code_image_path, "rb") as image_file:
        qr_code_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    # Define the context for the HTML template
    context = {
        'table_number': table.number,
        'restaurant_name': table.restaurant.restaurant_name,
        'qr_code_image_base64': qr_code_image_base64,
    }

    # Render the HTML template to a string
    html = render_to_string('restau_panel/qr_download_template.html', context)

    # Create a BytesIO buffer to hold the PDF data
    buffer = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), buffer)

    # If PDF generation is successful, return the response
    if not pdf.err:
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="table_{table.number}_qr_code.pdf"'
        return response

    # If there's an error, return a simple HTTP response
    return HttpResponse("Error generating PDF", status=500)

def delete_qr_code(request, table_id):
    # Fetch the table object
    try:
        table = get_object_or_404(restaurantTable, id=table_id)
        table.delete()
        return redirect("restau-tables")
    except Exception as e:
        print(str(e))
        return HttpResponse("Error deleting table", status=500)
    return HttpResponse(table.number)