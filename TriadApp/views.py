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
from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
import time

User = get_user_model()

def index(request):
    return render(request, 'TriadApp/index.html')

@superuser_required
def super_admin(request):
    # Get the fresh user data from the database
    super_admin = CustomUser.objects.get(id=request.user.id)
    context = {
        'super_admin': super_admin
    }
    return render(request, 'TriadApp/superadmin/super_admin.html', context)




def login_page(request):
    return render(request, 'TriadApp/login.html')



def logout_view(request):
    # Get the user's name before logging out
    if request.session.get('admin_name'):
        name = request.session.get('admin_name')
    elif request.user.is_authenticated:
        name = request.user.first_name
    else:
        name = "User"
    
    # Clear all session data and logout
    logout(request)
    request.session.flush()
    
    # Store logout message in session
    request.session['logout_message'] = f"Goodbye, {name}!"
    
    return redirect('login')



def register_admin(request):
    return render(request, 'TriadApp/superadmin/register_admin.html')



def superadmin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check login attempts
        attempts_key = f'login_attempts_{username}'
        block_key = f'login_blocked_{username}'
        block_time_key = f'login_blocked_time_{username}'
        
        # Check if user is blocked
        if cache.get(block_key):
            current_time = time.time()
            block_start_time = cache.get(block_time_key)
            remaining_time = int(300 - (current_time - block_start_time))
            
            if remaining_time > 0:
                return JsonResponse({
                    'success': False,
                    'locked': True,
                    'message': 'Too many failed attempts. Account locked.',
                    'remaining_time': remaining_time
                })
            else:
                # Reset if time has expired
                cache.delete(block_key)
                cache.delete(block_time_key)

        try:
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_superuser:
                cache.delete(attempts_key)
                cache.delete(block_key)
                cache.delete(block_time_key)
                
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': f"Welcome, {user.first_name}!",
                    'redirect_url': reverse('super_admin')
                })
            else:
                attempts = cache.get(attempts_key, 0) + 1
                cache.set(attempts_key, attempts, 300)

                if attempts >= 3:
                    cache.set(block_key, True, 300)
                    cache.set(block_time_key, time.time(), 300)
                    cache.delete(attempts_key)
                    return JsonResponse({
                        'success': False,
                        'locked': True,
                        'message': 'Too many failed attempts. Account locked for 5 minutes.',
                        'remaining_time': 300
                    })
                
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid credentials. {3 - attempts} attempts remaining.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return render(request, 'TriadApp/login.html')




def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check login attempts
        attempts_key = f'login_attempts_{username}'
        block_key = f'login_blocked_{username}'
        
        # Check if user is blocked
        if cache.get(block_key):
            time_remaining = cache.ttl(block_key)
            return JsonResponse({
                'success': False,
                'locked': True,
                'message': f'Account locked. Try again in {time_remaining} seconds.',
                'remaining_time': time_remaining
            })

        try:
            admin_profile = AdminProfile.objects.get(username=username)
            if check_password(password, admin_profile.password):
                # Reset attempts on successful login
                cache.delete(attempts_key)
                cache.delete(block_key)
                
                request.session['admin_id'] = admin_profile.id
                request.session['admin_name'] = f"{admin_profile.firstname} {admin_profile.lastname}"
                request.session['stall_id'] = str(admin_profile.stall.store_id)
                request.session['is_admin'] = True
                
                return JsonResponse({
                    'success': True,
                    'message': f"Welcome, {admin_profile.firstname}!",
                    'redirect_url': reverse('admin_dashboard')
                })
            else:
                # Increment failed attempts
                attempts = cache.get(attempts_key, 0) + 1
                cache.set(attempts_key, attempts, 300)  # 5 minutes expiry

                if attempts >= 3:
                    cache.set(block_key, True, 300)  # 5 minutes block
                    cache.delete(attempts_key)
                    return JsonResponse({
                        'success': False,
                        'locked': True,
                        'message': 'Too many failed attempts. Account locked for 5 minutes.',
                        'remaining_time': 300
                    })
                
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid password. {3 - attempts} attempts remaining.'
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
                return JsonResponse({
                    'success': False, 
                    'message': 'No account found with this email address'
                })
            
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
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while processing your request'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

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

@csrf_exempt
def send_contact(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            message = data.get('message')
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f9f9f9;
                        border-radius: 10px;
                    }}
                    .header {{
                        background-color: #1a56db;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 0 0 10px 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        color: #666;
                        font-size: 12px;
                    }}
                    .info-label {{
                        font-weight: bold;
                        color: #1a56db;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Contact Form Submission</h1>
                    </div>
                    <div class="content">
                        <p><span class="info-label">Name:</span> {name}</p>
                        <p><span class="info-label">Email:</span> {email}</p>
                        <p><span class="info-label">Message:</span></p>
                        <p style="white-space: pre-line;">{message}</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from the I/O Food Hub contact form.</p>
                        <p>&copy; 2024 I/O Food Hub. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version for email clients that don't support HTML
            plain_message = f"""
            New Contact Form Submission

            Name: {name}
            Email: {email}
            Message:
            {message}

            This email was sent from the I/O Food Hub contact form.
            """
            
            send_mail(
                subject='New Contact Form Submission - I/O Food Hub',
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['kentrixcapstone@gmail.com'],
                fail_silently=False,
                html_message=html_message
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_login_attempts(ip):
    attempts = cache.get(f'login_attempts_{ip}', 0)
    if attempts >= 3:
        last_attempt = cache.get(f'last_attempt_{ip}')
        if last_attempt:
            time_passed = datetime.now() - last_attempt
            if time_passed < timedelta(minutes=5):
                remaining = 300 - time_passed.seconds  # 300 seconds = 5 minutes
                return False, remaining
    return True, 0

def increment_login_attempts(ip):
    attempts = cache.get(f'login_attempts_{ip}', 0)
    attempts += 1
    cache.set(f'login_attempts_{ip}', attempts, 300)  # Reset after 5 minutes
    cache.set(f'last_attempt_{ip}', datetime.now(), 300)
    return attempts

def reset_login_attempts(ip):
    cache.delete(f'login_attempts_{ip}')
    cache.delete(f'last_attempt_{ip}')

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check login attempts
        attempts_key = f'login_attempts_{username}'
        block_key = f'login_blocked_{username}'
        block_time_key = f'login_blocked_time_{username}'
        
        if cache.get(block_key):
            current_time = time.time()
            block_start_time = cache.get(block_time_key)
            remaining_time = int(300 - (current_time - block_start_time))
            
            if remaining_time > 0:
                return JsonResponse({
                    'success': False,
                    'locked': True,
                    'message': 'Too many failed attempts. Account locked.',
                    'remaining_time': remaining_time
                })
            else:
                cache.delete(block_key)
                cache.delete(block_time_key)

        try:
            # Try CustomUser (Superadmin/Employee) first
            try:
                user = CustomUser.objects.get(username=username)
                if user.check_password(password):
                    if user.is_superuser:
                        login(request, user)
                        cache.delete(attempts_key)
                        cache.delete(block_key)
                        cache.delete(block_time_key)
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse('super_admin'),
                            'name': user.first_name
                        })
                    else:
                        login(request, user)
                        cache.delete(attempts_key)
                        cache.delete(block_key)
                        cache.delete(block_time_key)
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse('employee_dashboard'),
                            'name': user.first_name
                        })
            except CustomUser.DoesNotExist:
                pass

            # Try AdminProfile
            try:
                admin = AdminProfile.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['admin_id'] = admin.id
                    request.session['admin_name'] = f"{admin.firstname} {admin.lastname}"
                    request.session['stall_id'] = str(admin.stall.store_id)
                    request.session['is_admin'] = True
                    cache.delete(attempts_key)
                    cache.delete(block_key)
                    cache.delete(block_time_key)
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('admin_dashboard'),
                        'name': f"{admin.firstname} {admin.lastname}"
                    })
            except AdminProfile.DoesNotExist:
                pass

            # If we get here, increment failed attempts
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, 300)

            if attempts >= 3:
                cache.set(block_key, True, 300)
                cache.set(block_time_key, time.time(), 300)
                cache.delete(attempts_key)
                return JsonResponse({
                    'success': False,
                    'locked': True,
                    'message': 'Too many failed attempts. Account locked for 5 minutes.',
                    'remaining_time': 300
                })
            
            return JsonResponse({
                'success': False,
                'message': f'Invalid credentials. {3 - attempts} attempts remaining.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return render(request, 'TriadApp/login.html')