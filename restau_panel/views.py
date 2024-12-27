from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required  
from Home.models import RestaurantSubscription 
from restau_panel.models import restaurantMenuCategory

# Create your views here.

@login_required(login_url="restaurant-login")
def restauLogin(request):
    return render(request, 'restau_panel/restau_login.html')
    

@login_required(login_url="restaurant-login")
def restauDashboard(request):
    return render(request, 'restau_panel/dashboard.html')

@login_required(login_url="restaurant-login")
def restauMenu(request):   
    return render(request, 'restau_panel/menu.html')



@login_required(login_url="restaurant-login")
def restauAddCategory(request):
    if request.method == 'POST':
        restaurant = request.user
        try:
            restaurant_obj = RestaurantSubscription.objects.get(restaurant=restaurant)
            category_name = request.POST.get("category_name")
            category_description = request.POST.get("category_description")

            # Save category
            restaurantMenuCategory.objects.create(
                restaurant=restaurant_obj,
                name=category_name,
                description=category_description
            )
            return JsonResponse({"success": True, "message": "Category added successfully."})
        except Exception as e:
            print(str(e))
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})

        
        


@login_required(login_url="restaurant-login")
def restauOrders(request):
    return render(request, 'restau_panel/orders.html')

@login_required(login_url="restaurant-login")
def restauCustomerReviews(request):
    return render(request, 'restau_panel/customer-reviews.html')


@login_required(login_url="restaurant-login")
def restauTables(request):
    return render(request, 'restau_panel/tables.html')