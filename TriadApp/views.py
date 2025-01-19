from django.shortcuts import render, redirect
from django.contrib import messages
import pyrebase
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import AdminProfile, CustomUser, LoginHistory, Employee
from django.contrib.auth import authenticate, login
from .decorators import *
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

from django.http import HttpResponse
from django.views.decorators.http import require_POST
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




@admin_required
def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    is_admin = request.session.get('is_admin', False)
    
    if not admin_id or not is_admin:
        request.session.flush()
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        context = {
            'admin': admin,
            'stall': admin.stall,
        }
        return render(request, 'TriadApp/admin/admin.html', context)
    except AdminProfile.DoesNotExist:
        request.session.flush()
        return redirect('login')



@employee_login_required  # Replace @login_required with this
def employee_dashboard(request):
    employee_id = request.session.get('employee_id')
    is_employee = request.session.get('is_employee', False)
    
    if not employee_id or not is_employee:
        request.session.flush()
        return redirect('login')
    
    try:
        employee = Employee.objects.get(id=employee_id)
        
        # Check if employee is active
        if not employee.is_active:
            request.session.flush()
            messages.error(request, 'Your account has been deactivated. Please contact your administrator.')
            return redirect('login')
        
        # Check if stall is active
        if not employee.stall.is_active:
            request.session.flush()
            messages.error(request, 'Your stall is currently inactive. Please contact your administrator.')
            return redirect('login')
        
        context = {
            'employee': employee,
            'stall': employee.stall,
        }
        return render(request, 'TriadApp/employee/employee.html', context)
    except Employee.DoesNotExist:
        request.session.flush()
        return redirect('login')

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
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
        
        # Get system information
        system_info = LoginHistory.get_system_info()
        
        # Create base login history entry
        current_attempts = cache.get(attempts_key, 0)
        login_history = LoginHistory(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            attempt_count=current_attempts + 1,
            **system_info
        )
        
        try:
            # Try CustomUser (Superadmin) first
            try:
                user = CustomUser.objects.get(username=username)
                if user.check_password(password):
                    login(request, user)
                    login_history.user = user
                    login_history.status = 'success'
                    login_history.save()
                    
                    cache.delete(attempts_key)
                    cache.delete(block_key)
                    cache.delete(block_time_key)
                    
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('super_admin'),
                        'name': user.first_name
                    })
            except CustomUser.DoesNotExist:
                pass
                
            # Try AdminProfile
            try:
                admin = AdminProfile.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['admin_id'] = admin.id
                    request.session['is_admin'] = True
                    request.session.save()
                    
                    login_history.admin_profile = admin
                    login_history.status = 'success'
                    login_history.save()
                    
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
            
            # Try Employee
            try:
                employee = Employee.objects.get(username=username)
                if password == employee.raw_password:
                    # Check if employee is active
                    if not employee.is_active:
                        login_history.status = 'failed'
                        login_history.save()
                        return JsonResponse({
                            'success': False,
                            'message': 'Your account has been deactivated. Please contact your administrator.'
                        })
                    
                    # Check if stall is active
                    if not employee.stall.is_active:
                        login_history.status = 'failed'
                        login_history.save()
                        return JsonResponse({
                            'success': False,
                            'message': 'Your stall is currently inactive. Please contact your administrator.'
                        })
                    
                    # Check if stall's contract is expired
                   
                    
                    request.session['employee_id'] = employee.id
                    request.session['is_employee'] = True
                    request.session.save()
                    
                    login_history.employee = employee
                    login_history.status = 'success'
                    login_history.save()
                    
                    cache.delete(attempts_key)
                    cache.delete(block_key)
                    cache.delete(block_time_key)
                    
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('employee_dashboard'),
                        'name': f"{employee.firstname} {employee.lastname}"
                    })
            except Employee.DoesNotExist:
                pass
            
            # If we get here, login failed
            current_attempts += 1
            cache.set(attempts_key, current_attempts, 300)  # Expire after 5 minutes
            
            # Check if we should block the account
            if current_attempts >= 3:
                cache.set(block_key, True, 300)
                cache.set(block_time_key, time.time(), 300)
                login_history.is_blocked = True
                login_history.block_expires = timezone.now() + timedelta(minutes=5)
            
            login_history.status = 'failed'
            login_history.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'attempts_left': 3 - current_attempts if current_attempts < 3 else 0
            })
            
        except Exception as e:
            login_history.status = 'error'
            login_history.save()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return render(request, 'TriadApp/login.html')



def logout_view(request):
    # Get the user's name before logging out
    if request.session.get('admin_name'):
        name = request.session.get('admin_name')
    elif request.user.is_authenticated:
        name = request.user.first_name
    else:
        name = "User"
    
    # Store logout message in a temporary variable
    logout_message = f"Goodbye, {name}!"
    
    # Clear all session data and logout
    logout(request)
    request.session.flush()
    
    # Create a new session for the logout message only
    request.session['logout_message'] = logout_message
    request.session['show_once'] = True  # Add a flag to show message only once
    
    return redirect('login')


@require_POST
def clear_session(request):
    # Clear only the logout message and show_once flag
    request.session.pop('logout_message', None)
    request.session.pop('show_once', None)
    return HttpResponse('Session cleared')


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
