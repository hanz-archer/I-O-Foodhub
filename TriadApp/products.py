
from django.shortcuts import render, redirect
from django.contrib import messages
import pyrebase

from .models import Stall
from django.core.files.images import ImageFile




from django.shortcuts import render
from django.core.files.images import ImageFile
from .models import Stall

def add_stall(request):
    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        logo = request.FILES.get("logo")  # For file uploads
        
        try:
            # Create and save the stall
            stall = Stall(name=name, logo=logo, contact_number=contact_number)
            stall.save()

            context = {
                "success": True,
                "message": "Stall created successfully!",
                "store_id": stall.store_id,
            }
        except Exception as e:
            context = {
                "success": False,
                "message": f"Error: {str(e)}",
            }
    else:
        context = {}

    return render(request, "TriadApp/superadmin/add_stall.html", context)










def inventory(request):
    return render(request, 'TriadApp/admin/admin-inventory.html')
def add_product(request):
   

    return render(request, 'TriadApp/admin/admin-inventory.html')
