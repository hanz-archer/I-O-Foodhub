from django.shortcuts import render, redirect
from django.contrib import messages
from .decorators import superuser_required










@superuser_required
def inventory(request):
    return render(request, 'TriadApp/admin/admin-inventory.html')

@superuser_required
def add_product(request):
   

    return render(request, 'TriadApp/admin/admin-inventory.html')
