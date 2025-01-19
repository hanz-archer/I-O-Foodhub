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
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import os
import time
from datetime import datetime, date
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import StallContract, StallPayment
from decimal import Decimal
from django.db import transaction
CustomUser = get_user_model()


@superuser_required
def super_admin_profile(request):
    return render(request, 'TriadApp/superadmin/super_admin_profile.html', {
        'user': request.user,
        'super_admin': request.user
    })

@superuser_required
def update_super_admin_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            
            # Handle profile image upload
            if 'profile_image' in request.FILES:
                # Delete old image if it exists
                if user.profile_image:
                    try:
                        old_image_path = user.profile_image.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

                # Save new image
                user.profile_image = request.FILES['profile_image']
                user.save()

                # Return success with new image URL
                return JsonResponse({
                    'success': True,
                    'message': 'Profile picture updated successfully!',
                    'image_url': user.profile_image.url + f"?t={int(time.time())}"
                })
            
            # Handle other profile updates
            if request.POST:
                user.first_name = request.POST.get('firstname', user.first_name)
                user.middle_name = request.POST.get('middle_name', user.middle_name)
                user.last_name = request.POST.get('lastname', user.last_name)
                user.email = request.POST.get('email', user.email)
                user.username = request.POST.get('username', user.username)
                user.gender = request.POST.get('gender', user.gender)
                user.phone = request.POST.get('phone', user.phone)
                user.address = request.POST.get('address', user.address)
                
                birthdate = request.POST.get('birthdate')
                if birthdate:
                    user.birthdate = birthdate
                
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!'
                })
            
        except Exception as e:
            print(f"Error in update_super_admin_profile: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error updating profile: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })



@superuser_required
def add_stall(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create Stall
                stall = Stall.objects.create(
                    name=request.POST.get('name'),
                    contact_number=request.POST.get('contact_number'),
                    logo=request.FILES.get('logo'),
                    is_active=True  # Set active since contract will be created
                )
                
                # Create Contract
                contract = StallContract.objects.create(
                    stall=stall,
                    start_date=request.POST.get('start_date'),
                    duration_months=int(request.POST.get('duration_months')),
                    monthly_rate=Decimal(request.POST.get('monthly_rate'))
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Stall and contract created successfully',
                    'redirect_url': reverse('manage_contracts')
                })
                
        except Exception as e:
            print(f"Error creating stall: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            })
    
    # Add stalls to context without ordering by created_at
    stalls = Stall.objects.all()
    context = {
        'current_date': timezone.now().date(),
        'super_admin': request.user,
        'stalls': stalls
    }
    return render(request, 'TriadApp/superadmin/add_stall.html', context)





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
        birthdate = request.POST.get('birthdate')
        
        # Calculate age from birthdate
        birth_date = datetime.strptime(birthdate, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Validate age
        if age < 15:
            messages.error(request, 'Admin must be at least 15 years old')
            return redirect('register_admin')
            
        # Check for exact duplicate full names (allowing same first names)
        if middle_initial:
            name_exists = AdminProfile.objects.filter(
                firstname__iexact=firstname,
                middle_initial__iexact=middle_initial,
                lastname__iexact=lastname
            ).exists()
        else:
            name_exists = AdminProfile.objects.filter(
                firstname__iexact=firstname,
                middle_initial__isnull=True,
                lastname__iexact=lastname
            ).exists()
            
        if name_exists:
            messages.error(request, 'An admin with this exact full name already exists')
            return redirect('register_admin')
            
        address = request.POST.get('address')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact_number = request.POST.get('contact_number')
        stall_id = request.POST.get('stall')

        try:
            # Check if username exists in CustomUser (superadmin/employees)
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists in the system')
                return redirect('register_admin')
            
            # Check if username exists in AdminProfile
            if AdminProfile.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists in admin profiles')
                return redirect('register_admin')
            
            # Check if email exists in CustomUser
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists in the system')
                return redirect('register_admin')
            
            # Check if email exists in AdminProfile
            if AdminProfile.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists in admin profiles')
                return redirect('register_admin')
            
            # Check stall availability
            stall = Stall.objects.get(store_id=stall_id)
            if AdminProfile.objects.filter(stall=stall).exists():
                messages.error(request, f'Stall {stall.name} already has an admin assigned')
                return redirect('register_admin')
            
            hashed_password = make_password(password)
            
            AdminProfile.objects.create(
                firstname=firstname,
                middle_initial=middle_initial,
                lastname=lastname,
                age=age,
                birthdate=birthdate,
                address=address,
                username=username,
                email=email,
                password=hashed_password,
                contact_number=contact_number,
                stall=stall
            )
            messages.success(request, 'Admin successfully registered!')
            return redirect('register_admin')
            
        except Stall.DoesNotExist:
            messages.error(request, 'Stall not found')
            return redirect('register_admin')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('register_admin')

    # Get available stalls
    stalls = Stall.objects.exclude(
        store_id__in=AdminProfile.objects.values_list('stall__store_id', flat=True)
    )
    admins = AdminProfile.objects.all()
    return render(request, 'TriadApp/superadmin/register_admin.html', {
        'stalls': stalls,
        'admins': admins,
        'super_admin': request.user
    })



@superuser_required
def edit_admin(request):
    if request.method == 'POST':
        try:
            admin_id = request.POST.get('admin_id')
            admin = get_object_or_404(AdminProfile, id=admin_id)
            
            firstname = request.POST.get('firstname')
            middle_initial = request.POST.get('middle_initial')
            lastname = request.POST.get('lastname')
            
            # Check for exact duplicate full names (allowing same first names)
            if middle_initial:
                name_exists = AdminProfile.objects.filter(
                    firstname__iexact=firstname,
                    middle_initial__iexact=middle_initial,
                    lastname__iexact=lastname
                ).exclude(id=admin_id).exists()
            else:
                name_exists = AdminProfile.objects.filter(
                    firstname__iexact=firstname,
                    middle_initial__isnull=True,
                    lastname__iexact=lastname
                ).exclude(id=admin_id).exists()
            
            if name_exists:
                return JsonResponse({
                    'success': False,
                    'message': 'An admin with this exact full name already exists'
                })
            
            birthdate = request.POST.get('birthdate')
            # Calculate age from birthdate
            birth_date = datetime.strptime(birthdate, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            # Validate age
            if age < 15:
                return JsonResponse({
                    'success': False,
                    'message': 'Admin must be at least 15 years old'
                })
            
            address = request.POST.get('address')
            username = request.POST.get('username')
            email = request.POST.get('email')
            contact_number = request.POST.get('contact_number')
            new_stall_id = request.POST.get('stall')
            new_password = request.POST.get('password')

            # Rest of your validation code...

            # Update admin details
            admin.firstname = firstname
            admin.middle_initial = middle_initial
            admin.lastname = lastname
            admin.age = age  # Use calculated age
            admin.birthdate = birthdate
            admin.address = address
            admin.username = username
            admin.email = email
            admin.contact_number = contact_number

            if new_password and new_password.strip():
                admin.password = make_password(new_password)

            admin.save()

            return JsonResponse({
                'success': True,
                'message': 'Admin profile updated successfully!',
                'data': {
                    'id': admin.id,
                    'firstname': admin.firstname,
                    'middle_initial': admin.middle_initial,
                    'lastname': admin.lastname,
                    'age': age,  # Return calculated age
                    'birthdate': admin.birthdate,
                    'address': admin.address,
                    'username': admin.username,
                    'email': admin.email,
                    'contact_number': admin.contact_number,
                    'stall_name': admin.stall.name,
                    'stall_id': admin.stall.store_id
                }
            })

        except Exception as e:
            print(f"Error in edit_admin: {str(e)}")
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
def stall_contract(request, store_id):
    stall = get_object_or_404(Stall, store_id=store_id)
    contracts = StallContract.objects.filter(stall=stall).prefetch_related('payments')
    
    # Get the latest/active contract
    current_contract = contracts.first() if contracts.exists() else None
    
    # Calculate payment statistics if there's an active contract
    if current_contract:
        payments = current_contract.payments.all().order_by('-payment_date')
        total_amount = current_contract.monthly_rate * current_contract.duration_months
        total_paid = sum(payment.amount_paid for payment in payments)
        remaining_balance = total_amount - total_paid
    else:
        payments = []
        total_amount = total_paid = remaining_balance = 0
    
    context = {
        'stall': stall,
        'contract': current_contract,
        'payments': payments,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'current_date': timezone.now().date(),
        'super_admin': request.user
    }
    return render(request, 'TriadApp/superadmin/stall_contract.html', context)

@superuser_required
def add_stall_payment(request, store_id, contract_id):
    if request.method == 'POST':
        try:
            stall = get_object_or_404(Stall, store_id=store_id)
            contract = get_object_or_404(StallContract, id=contract_id, stall=stall)
            
            payment_date = request.POST.get('payment_date')
            amount = request.POST.get('amount')
            payment_method = request.POST.get('payment_method')
            payment_for_month = request.POST.get('payment_for_month')
            notes = request.POST.get('notes')
            
            payment = StallPayment.objects.create(
                contract=contract,
                payment_date=payment_date,
                amount_paid=amount,
                payment_method=payment_method,
                payment_for_month=payment_for_month,
                notes=notes
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment recorded successfully',
                'receipt_number': payment.receipt_number
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@superuser_required
def manage_contracts(request):
    # Get all contracts with their stalls and payments
    contracts = StallContract.objects.all().select_related('stall').prefetch_related('payments')
    # Get active stalls without contracts for the dropdown
    stalls = Stall.objects.filter(is_active=True).exclude(
        id__in=StallContract.objects.filter(
            end_date__gte=timezone.now().date()
        ).values('stall_id')
    )
    
    context = {
        'contracts': contracts,
        'stalls': stalls,
        'current_date': timezone.now().date(),
        'super_admin': request.user
    }
    return render(request, 'TriadApp/superadmin/contracts.html', context)

@superuser_required
def add_stall_contract(request):
    if request.method == 'POST':
        try:
            stall_id = request.POST.get('stall')
            stall = get_object_or_404(Stall, store_id=stall_id)
            
            # Check if stall already has an active contract
            existing_contract = StallContract.objects.filter(
                stall=stall,
                end_date__gte=timezone.now().date()
            ).first()
            
            if existing_contract:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This stall already has an active contract'
                })
            
            start_date = request.POST.get('start_date')
            duration_months = int(request.POST.get('duration_months'))
            monthly_rate = Decimal(request.POST.get('monthly_rate'))
            
            # Validate start date
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if start_date < timezone.now().date():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Start date cannot be in the past'
                })
            
            contract = StallContract.objects.create(
                stall=stall,
                start_date=start_date,
                duration_months=duration_months,
                monthly_rate=monthly_rate
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Contract created successfully',
                'redirect_url': reverse('manage_contracts')
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid input values'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@superuser_required
def contract_details(request, contract_id):
    contract = get_object_or_404(StallContract.objects.select_related('stall'), id=contract_id)
    payments = contract.payments.all().order_by('-payment_date')
    
    total_paid = sum(payment.amount_paid for payment in payments)
    remaining_balance = contract.total_amount - total_paid
    
    context = {
        'contract': contract,
        'payments': payments,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'super_admin': request.user
    }
    return render(request, 'TriadApp/superadmin/contract_details.html', context)

@superuser_required
def add_payment(request, contract_id):
    if request.method == 'POST':
        try:
            contract = get_object_or_404(StallContract, id=contract_id)
            
            payment_date = datetime.strptime(request.POST.get('payment_date'), '%Y-%m-%d').date()
            amount = Decimal(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')
            payment_for_month = datetime.strptime(request.POST.get('payment_for_month'), '%Y-%m').date()
            notes = request.POST.get('notes', '')
            
            # Validate payment date
            if payment_date > timezone.now().date():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment date cannot be in the future'
                })
            
            # Validate payment amount
            total_paid = sum(p.amount_paid for p in contract.payments.all())
            remaining_balance = contract.total_amount - total_paid
            
            if amount > remaining_balance:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Payment amount exceeds remaining balance (₱{remaining_balance})'
                })
            
            payment = StallPayment.objects.create(
                contract=contract,
                payment_date=payment_date,
                amount_paid=amount,
                payment_method=payment_method,
                payment_for_month=payment_for_month,
                notes=notes
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment recorded successfully',
                'receipt_number': payment.receipt_number
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid input values'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


