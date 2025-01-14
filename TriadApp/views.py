from django.shortcuts import render, redirect
from django.contrib import messages
import pyrebase
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import AdminProfile
from django.contrib.auth import authenticate, login
from .decorators import superuser_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def index(request):
    return render(request, 'TriadApp/index.html')

@superuser_required
def super_admin(request):
    return render(request, 'TriadApp/superadmin/super_admin.html')


def admin(request):
    return render(request, 'TriadApp/admin/admin.html')


def login_page(request):
    return render(request, 'TriadApp/login.html')



def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('index')  # Replace 'login' with your login URL name



def register_admin(request):
    return render(request, 'TriadApp/superadmin/register_admin.html')



def superadmin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)  # Now this will use Django's login function
            return redirect('super_admin')
        else:
            messages.error(request, 'Invalid credentials or not authorized as Superadmin.')
    
    return render(request, 'TriadApp/login.html')




def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Retrieve the admin profile with the provided username
            admin_profile = AdminProfile.objects.get(username=username)

            # Verify the password
            if check_password(password, admin_profile.password):
                # Store admin details in the session
                request.session['admin_id'] = admin_profile.id
                request.session['admin_name'] = f"{admin_profile.firstname} {admin_profile.lastname}"
                messages.success(request, f"Welcome, {admin_profile.firstname}!")
                return redirect('superadmin')  # Replace with your admin dashboard URL
            else:
                messages.error(request, "Invalid username or password.")
        except AdminProfile.DoesNotExist:
            messages.error(request, "Admin does not exist.")
    
    return render(request, 'TriadApp/login.html')


def employee_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)  # Now this will use Django's login function
            return redirect('superadmin')
        else:
            messages.error(request, 'Invalid credentials or not authorized as Superadmin.')
    
    return render(request, 'TriadApp/login.html')

@superuser_required
def super_admin_profile(request):
    return render(request, 'TriadApp/superadmin/super_admin_profile.html', {
        'user': request.user
    })

@superuser_required
def update_super_admin_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Update profile image if provided
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        # Update other fields
        user.firstname = request.POST.get('firstname', user.firstname)
        user.middle_name = request.POST.get('middle_name', user.middle_name)
        user.lastname = request.POST.get('lastname', user.lastname)
        user.birthdate = request.POST.get('birthdate', user.birthdate)
        user.address = request.POST.get('address', user.address)
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        
        # Update password if provided
        if request.POST.get('password'):
            user.set_password(request.POST['password'])
        
        try:
            user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})