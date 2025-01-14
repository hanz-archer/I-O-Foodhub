from django.core.files.images import ImageFile
from .models import Stall
from .models import AdminProfile, Stall
from django.contrib.auth.hashers import make_password

from django.shortcuts import render, redirect




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














def register_admin(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        middle_initial = request.POST.get('middle_initial')
        lastname = request.POST.get('lastname')
        age = request.POST.get('age')
        birthdate = request.POST.get('birthdate')
        address = request.POST.get('address')
        username = request.POST.get('username')
        password = request.POST.get('password')
        contact_number = request.POST.get('contact_number')
        stall_id = request.POST.get('stall')

        try:
            stall = Stall.objects.get(id=stall_id)
            AdminProfile.objects.create(
                firstname=firstname,
                middle_initial=middle_initial,
                lastname=lastname,
                age=age,
                birthdate=birthdate,
                address=address,
                username=username,
                password=password,  # Use proper password hashing
                contact_number=contact_number,
                stall=stall
            )
            return redirect('admin_records')
        except Stall.DoesNotExist:
            return render(request, 'error.html', {'message': 'Stall not found'})

    stalls = Stall.objects.all()
    return render(request, 'TriadApp/superadmin/register_admin.html', {'stalls': stalls})
