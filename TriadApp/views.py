from django.shortcuts import render, redirect
from django.contrib import messages
import pyrebase
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import AdminProfile, CustomUser
from django.contrib.auth import authenticate, login
from .decorators import superuser_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
import random
import string
from django.core.mail import send_mail
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

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
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': f"Welcome, {user.first_name}!",
                'redirect': reverse('super_admin')
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials or not authorized as Superadmin'
            })
    
    return render(request, 'TriadApp/login.html')




def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            admin_profile = AdminProfile.objects.get(username=username)
            if check_password(password, admin_profile.password):
                request.session['admin_id'] = admin_profile.id
                request.session['admin_name'] = f"{admin_profile.firstname} {admin_profile.lastname}"
                return JsonResponse({
                    'success': True,
                    'message': f"Welcome, {admin_profile.firstname}!",
                    'redirect': reverse('admin')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': "Invalid password"
                })
        except AdminProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Admin account not found"
            })
    
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
        
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        user.firstname = request.POST.get('firstname', user.firstname)
        user.middle_name = request.POST.get('middle_name', user.middle_name)
        user.lastname = request.POST.get('lastname', user.lastname)
        user.birthdate = request.POST.get('birthdate', user.birthdate)
        user.address = request.POST.get('address', user.address)
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        
        if request.POST.get('password'):
            user.set_password(request.POST['password'])
        
        try:
            user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def forgot_password(request):
    return render(request, 'TriadApp/forgot_password.html')

@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        try:
            # Check each user type
            user = CustomUser.objects.filter(email=email).first()
            admin = AdminProfile.objects.filter(email=email).first()
            
            if not user and not admin:
                return JsonResponse({'success': False, 'message': 'Email not found'})
            
            # Determine user type for the message
            user_type = 'Super Admin' if (user and user.is_superuser) else \
                       'Employee' if user else \
                       'Admin' if admin else 'Unknown'
            
            otp = generate_otp()
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #E8E3D7; padding: 20px; text-align: center; }}
                    .content {{ background-color: #ffffff; padding: 20px; border-radius: 5px; }}
                    .otp-box {{ background-color: #f8f8f8; padding: 15px; text-align: center; 
                               font-size: 24px; letter-spacing: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>I/O FoodHub</h1>
                    </div>
                    <div class="content">
                        <h2>Password Reset Request - {user_type}</h2>
                        <p>Hello,</p>
                        <p>We received a request to reset your {user_type} account password. Please use the following OTP code to proceed:</p>
                        <div class="otp-box">
                            <strong>{otp}</strong>
                        </div>
                        <p>This OTP will expire in 10 minutes for security purposes.</p>
                        <p>If you didn't request this password reset, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply.</p>
                        <p>&copy; 2024 I/O FoodHub. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_mail(
                f'Password Reset OTP - I/O FoodHub ({user_type})',
                f'Your OTP for password reset is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
                html_message=html_message
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')
        
        stored_otp = request.session.get('reset_otp')
        stored_email = request.session.get('reset_email')
        
        if email == stored_email and otp == stored_otp:
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'message': 'Invalid OTP'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        try:
            # Check for superuser/CustomUser
            user = CustomUser.objects.filter(email=email).first()
            if user:
                user.set_password(password)
                user.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Password reset successful!',
                    'redirect': 'superadmin_login' if user.is_superuser else 'employee_login'
                })
            
            # Check for admin
            admin = AdminProfile.objects.filter(email=email).first()
            if admin:
                admin.password = make_password(password)
                admin.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Password reset successful!',
                    'redirect': 'admin_login'
                })
            
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })