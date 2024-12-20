from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required   

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
def restauOrders(request):
    return render(request, 'restau_panel/orders.html')

@login_required(login_url="restaurant-login")
def restauCustomerReviews(request):
    return render(request, 'restau_panel/customer-reviews.html')


@login_required(login_url="restaurant-login")
def restauTables(request):
    return render(request, 'restau_panel/tables.html')