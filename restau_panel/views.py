from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from Home.models import RestaurantSubscription
from restau_panel.models import restaurantMenuCategory, restaurantMenuItems
from django.contrib import messages

# Create your views here.


@login_required(login_url="restaurant-login")
def restauLogin(request):
    return render(request, "restau_panel/restau_login.html")


@login_required(login_url="restaurant-login")
def restauDashboard(request):
    return render(request, "restau_panel/dashboard.html")


@login_required(login_url="restaurant-login")
def restauMenu(request):
    restaurant = request.user
    try:
        # Assuming the RestaurantMenuCategory model has a ForeignKey to Restaurant
        categories = restaurantMenuCategory.objects.filter(
            restaurant__restaurant=restaurant
        )
        menu_items = restaurantMenuItems.objects.filter(
            category__in=categories
        )  # Use __in for multiple categories
        print("Menu items", menu_items)
    except Exception as e:
        categories = []
        menu_items = []
        print(str(e))

    context = {"categories": categories, "menu_items": menu_items}
    return render(request, "restau_panel/menu.html", context)


@login_required(login_url="restaurant-login")
def restauAddCategory(request):
    if request.method == "POST":
        restaurant = request.user
        try:
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            category_name = request.POST.get("category_name")
            category_description = request.POST.get("category_description")

            # Save category
            restaurantMenuCategory.objects.create(
                restaurant=restaurant_obj,
                name=category_name,
                description=category_description,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Category added successfully. Reload the page to see the category",
                }
            )
        except Exception as e:
            print(str(e))
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


@login_required(login_url="restaurant-login")
def restauAddMenuItem(request):
    if request.method == "POST":
        try:
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

            restaurantMenuItems.objects.create(
                restaurant=restaurant_obj,
                category=restaurant_category,
                name=item_name,
                item_type=item_type,
                item_taste=item_taste,
                price=item_price,
            )

            return JsonResponse(
                {"success": True, "message": "Menu item added successfully!"}
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})



@login_required(login_url="restaurant-login")
def fetchMenuItemsByCategory(request):
    if request.method == "GET":
        category_id = request.GET.get("category_id")
        if not category_id:
            return JsonResponse(
                {"success": False, "error": "Category ID is required."}, status=400
            )

        try:
            category = restaurantMenuCategory.objects.get(id=category_id)
            menu_items = restaurantMenuItems.objects.filter(category=category)
            items_data = list(
                menu_items.values(
                    "name", "price", "item_type", "item_taste", "category__name"
                )
            )
            return JsonResponse({"success": True, "menu_items": items_data})

        except restaurantMenuCategory.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found."})

    return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required(login_url="restaurant-login")
def restauOrders(request):
    return render(request, "restau_panel/orders.html")


@login_required(login_url="restaurant-login")
def restauCustomerReviews(request):
    return render(request, "restau_panel/customer-reviews.html")


@login_required(login_url="restaurant-login")
def restauTables(request):
    return render(request, "restau_panel/tables.html")
