from django.core.files.images import ImageFile
from .models import Stall
from .models import AdminProfile, Stall
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.http import JsonResponse


from .models import Stall

def add_stall(request):
    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        logo = request.FILES.get("logo")  # For file uploads
        
        try:
            # Create and save the stall with is_active defaulting to True
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

    # Retrieve all stalls to display in the table
    stalls = Stall.objects.all()
    context["stalls"] = stalls

    return render(request, "TriadApp/superadmin/add_stall.html", context)






def edit_stall(request):
    """Handles editing a stall."""
    if request.method == 'POST':
        store_id = request.POST.get('store_id')
        name = request.POST.get('name')
        contact_number = request.POST.get('contact_number')
        logo = request.FILES.get('logo')
        is_active = request.POST.get('is_active') == 'on'  # Check if 'is_active' checkbox is checked

        # Get the stall based on store_id
        stall = get_object_or_404(Stall, store_id=store_id)
        
        # Update the stall details
        stall.name = name
        stall.contact_number = contact_number
        if logo:
            stall.logo = logo
        stall.is_active = is_active  # Update is_active status
        stall.save()

        return JsonResponse({'success': True, 'message': 'Stall updated successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def delete_stall(request, store_id):
    """Soft deletes a stall by setting is_active to False."""
    if request.method == "POST":
        stall = get_object_or_404(Stall, store_id=store_id)
        stall.is_active = False  # Mark the stall as inactive
        stall.save()
        return JsonResponse({'success': True, 'message': 'Stall deactivated successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})













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
