from django.core.files.images import ImageFile
from .models import Stall
from .models import AdminProfile, Stall
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from .models import Stall
from .decorators import superuser_required




@superuser_required
def add_stall(request):
    # First check if this is a redirect from a successful submission
    if request.method == "GET" and request.GET.get("success"):
        context = {
            "success": True,
            "message": request.GET.get("message"),
            "stalls": Stall.objects.all()
        }
        return render(request, "TriadApp/superadmin/add_stall.html", context)

    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        logo = request.FILES.get("logo")
        
        try:
            stall = Stall(name=name, logo=logo, contact_number=contact_number)
            stall.save()
            # Redirect after successful POST
            return redirect(f"{reverse('add_stall')}?success=true&message=Stall added successfully")
        except Exception as e:
            context = {
                "success": False,
                "message": f"Error: {str(e)}",
                "stalls": Stall.objects.all()
            }
            return render(request, "TriadApp/superadmin/add_stall.html", context)

    # Regular GET request
    return render(request, "TriadApp/superadmin/add_stall.html", {
        "stalls": Stall.objects.all()
    })





@superuser_required
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


@superuser_required
def delete_stall(request, store_id):
    """Deletes a stall from the database."""
    if request.method == "POST":
        stall = get_object_or_404(Stall, store_id=store_id)
        stall.delete()  # Actually delete from database
        return JsonResponse({'success': True, 'message': 'Stall deleted successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})














@superuser_required
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
            
            if AdminProfile.objects.filter(username=username).exists():
                return render(request, 'TriadApp/superadmin/register_admin.html', {
                    'error': 'Username already exists',
                    'stalls': Stall.objects.all(),
                    'admins': AdminProfile.objects.all()
                })
            
            hashed_password = make_password(password)
            
            AdminProfile.objects.create(
                firstname=firstname,
                middle_initial=middle_initial,
                lastname=lastname,
                age=age,
                birthdate=birthdate,
                address=address,
                username=username,
                password=hashed_password,
                contact_number=contact_number,
                stall=stall
            )
            return redirect('register_admin')
        except Stall.DoesNotExist:
            return render(request, 'TriadApp/superadmin/register_admin.html', {
                'error': 'Stall not found',
                'stalls': Stall.objects.all(),
                'admins': AdminProfile.objects.all()
            })

    # Get all stalls and admins for the template
    stalls = Stall.objects.all()
    admins = AdminProfile.objects.all()
    return render(request, 'TriadApp/superadmin/register_admin.html', {
        'stalls': stalls,
        'admins': admins
    })


@superuser_required
def edit_admin(request):
    """Handles editing an admin profile."""
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        firstname = request.POST.get('firstname')
        middle_initial = request.POST.get('middle_initial')
        lastname = request.POST.get('lastname')
        age = request.POST.get('age')
        birthdate = request.POST.get('birthdate')
        address = request.POST.get('address')
        username = request.POST.get('username')
        contact_number = request.POST.get('contact_number')
        stall_id = request.POST.get('stall')
        password = request.POST.get('password')  # Optional - only if changing password

        try:
            admin = get_object_or_404(AdminProfile, id=admin_id)
            stall = get_object_or_404(Stall, id=stall_id)

            # Check if username changed and if new username already exists
            if admin.username != username and AdminProfile.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                })

            # Update admin details
            admin.firstname = firstname
            admin.middle_initial = middle_initial
            admin.lastname = lastname
            admin.age = age
            admin.birthdate = birthdate
            admin.address = address
            admin.username = username
            admin.contact_number = contact_number
            admin.stall = stall

            # Only update password if provided
            if password:
                admin.password = make_password(password)

            admin.save()
            return JsonResponse({
                'success': True,
                'message': 'Admin profile updated successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating admin profile: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@superuser_required
def delete_admin(request, admin_id):
    """Deletes an admin profile."""
    if request.method == "POST":
        try:
            admin = get_object_or_404(AdminProfile, id=admin_id)
            admin.delete()
            return JsonResponse({
                'success': True,
                'message': 'Admin profile deleted successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting admin profile: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
@superuser_required
def add_stall(request):
    # First check if this is a redirect from a successful submission
    if request.method == "GET" and request.GET.get("success"):
        context = {
            "success": True,
            "message": request.GET.get("message"),
            "stalls": Stall.objects.all()
        }
        return render(request, "TriadApp/superadmin/add_stall.html", context)

    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        logo = request.FILES.get("logo")
        
        try:
            stall = Stall(name=name, logo=logo, contact_number=contact_number)
            stall.save()
            # Redirect after successful POST
            return redirect(f"{reverse('add_stall')}?success=true&message=Stall added successfully")
        except Exception as e:
            context = {
                "success": False,
                "message": f"Error: {str(e)}",
                "stalls": Stall.objects.all()
            }
            return render(request, "TriadApp/superadmin/add_stall.html", context)

    # Regular GET request
    return render(request, "TriadApp/superadmin/add_stall.html", {
        "stalls": Stall.objects.all()
    })

@superuser_required
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
            
            if AdminProfile.objects.filter(username=username).exists():
                return render(request, 'TriadApp/superadmin/register_admin.html', {
                    'error': 'Username already exists',
                    'stalls': Stall.objects.all(),
                    'admins': AdminProfile.objects.all()
                })
            
            hashed_password = make_password(password)
            
            AdminProfile.objects.create(
                firstname=firstname,
                middle_initial=middle_initial,
                lastname=lastname,
                age=age,
                birthdate=birthdate,
                address=address,
                username=username,
                password=hashed_password,
                contact_number=contact_number,
                stall=stall
            )
            return redirect('register_admin')
        except Stall.DoesNotExist:
            return render(request, 'TriadApp/superadmin/register_admin.html', {
                'error': 'Stall not found',
                'stalls': Stall.objects.all(),
                'admins': AdminProfile.objects.all()
            })

    # Get all stalls and admins for the template
    stalls = Stall.objects.all()
    admins = AdminProfile.objects.all()
    return render(request, 'TriadApp/superadmin/register_admin.html', {
        'stalls': stalls,
        'admins': admins
    })

@superuser_required
def edit_admin(request):
    """Handles editing an admin profile."""
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        firstname = request.POST.get('firstname')
        middle_initial = request.POST.get('middle_initial')
        lastname = request.POST.get('lastname')
        age = request.POST.get('age')
        birthdate = request.POST.get('birthdate')
        address = request.POST.get('address')
        username = request.POST.get('username')
        contact_number = request.POST.get('contact_number')
        stall_id = request.POST.get('stall')
        password = request.POST.get('password')  # Optional - only if changing password

        try:
            admin = get_object_or_404(AdminProfile, id=admin_id)
            stall = get_object_or_404(Stall, id=stall_id)

            # Check if username changed and if new username already exists
            if admin.username != username and AdminProfile.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                })

            # Update admin details
            admin.firstname = firstname
            admin.middle_initial = middle_initial
            admin.lastname = lastname
            admin.age = age
            admin.birthdate = birthdate
            admin.address = address
            admin.username = username
            admin.contact_number = contact_number
            admin.stall = stall

            # Only update password if provided
            if password:
                admin.password = make_password(password)

            admin.save()
            return JsonResponse({
                'success': True,
                'message': 'Admin profile updated successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating admin profile: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@superuser_required
def delete_admin(request, admin_id):
    """Deletes an admin profile."""
    if request.method == "POST":
        try:
            admin = get_object_or_404(AdminProfile, id=admin_id)
            admin.delete()
            return JsonResponse({
                'success': True,
                'message': 'Admin profile deleted successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting admin profile: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

