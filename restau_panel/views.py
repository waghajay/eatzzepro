from django.shortcuts import render
from django.http import HttpResponse    

# Create your views here.

def restauLogin(request):
    return render(request, 'restau_panel/restau_login.html')
    


def restauDashboard(request):
    
    return render(request, 'restau_panel/dashboard.html')


# def restauMenu(request):
#     return render(request, 'restau_panel/menu.html')



# def restauOrders(request):
#     return render(request, 'restau_panel/orders.html')