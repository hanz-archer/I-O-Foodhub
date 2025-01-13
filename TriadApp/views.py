
from django.shortcuts import render, redirect
from django.contrib import messages
import pyrebase
from .firebase import auth, database
from django.contrib.auth import authenticate, login

def index(request):
    return render(request, 'TriadApp/index.html')
        
def superadmin(request):
    return render(request, 'TriadApp/superadmin/super_admin.html')


def admin(request):
    return render(request, 'TriadApp/admin/admin.html')



def login(request):
    return render(request, 'TriadApp/login.html')


def superadmin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request)  # Use the correct Django login function
            return redirect('superadmin')  # Change to the actual dashboard URL
        else:
            messages.error(request, 'Invalid credentials or not authorized as Superadmin.')
    
    return render(request, 'TriadApp/login.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request)  # Use the correct Django login function
            return redirect('superadmin')  # Change to the actual dashboard URL
        else:
            messages.error(request, 'Invalid credentials or not authorized as Superadmin.')
    
    return render(request, 'TriadApp/login.html')

def employee_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request)  # Use the correct Django login function
            return redirect('superadmin')  # Change to the actual dashboard URL
        else:
            messages.error(request, 'Invalid credentials or not authorized as Superadmin.')
    
    return render(request, 'TriadApp/login.html')