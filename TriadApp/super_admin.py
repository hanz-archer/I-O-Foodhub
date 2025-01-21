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
from datetime import datetime, date, timedelta
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
            data_updated = False
            
            # Handle profile image upload
            if 'profile_image' in request.FILES:
                if user.profile_image:
                    try:
                        old_image_path = user.profile_image.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")
                
                user.profile_image = request.FILES['profile_image']
                data_updated = True

            # Handle other profile updates
            fields_to_update = {
                'first_name': 'firstname',
                'middle_name': 'middle_name',
                'last_name': 'lastname',
                'email': 'email',
                'username': 'username',
                'gender': 'gender',
                'phone': 'phone',
                'address': 'address',
            }

            for model_field, post_field in fields_to_update.items():
                if post_field in request.POST:
                    setattr(user, model_field, request.POST.get(post_field))
                    data_updated = True

            # Handle birthdate separately
            birthdate = request.POST.get('birthdate')
            if birthdate:
                try:
                    user.birthdate = birthdate
                    data_updated = True
                except Exception as e:
                    print(f"Error setting birthdate: {e}")

            # Handle password if provided
            new_password = request.POST.get('password')
            if new_password:
                user.set_password(new_password)
                data_updated = True

            if data_updated:
                user.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No changes detected'
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
    FIXED_MONTHLY_RATE = Decimal('5000.00')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create Stall (inactive by default)
                stall = Stall.objects.create(
                    name=request.POST.get('name'),
                    contact_number=request.POST.get('contact_number'),
                    logo=request.FILES.get('logo'),
                    is_active=False  # Set as inactive until first payment
                )
                
                # Create Contract with fixed rate
                contract = StallContract.objects.create(
                    stall=stall,
                    duration_months=int(request.POST.get('duration_months')),
                    monthly_rate=FIXED_MONTHLY_RATE,
                    payment_status='pending'
                    # Removed start_date since it's now nullable and will be set on first payment
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Stall created successfully. It will be activated upon full payment.',
                    'redirect_url': reverse('manage_contracts')
                })
                
        except Exception as e:
            print(f"Error creating stall: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            })
    
    stalls = Stall.objects.all()
    context = {
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
            
            hashed_password = make_password(request.POST.get('password'))
            
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
    current_date = timezone.now().date()
    
    # Get all contracts
    contracts = StallContract.objects.select_related('stall').all()
    
    # Process each contract to determine if it's active and handle expired contracts
    for contract in contracts:
        if not contract.start_date:
            contract.status = 'pending'
        else:
            contract_end = contract.start_date + timedelta(days=365)  # Fixed to 1 year
            if contract_end < current_date:
                # Contract has expired
                contract.status = 'expired'
                contract.payment_status = 'expired'
                contract.save()
                
                # Deactivate the stall
                if contract.stall.is_active:
                    contract.stall.is_active = False
                    contract.stall.save()
            else:
                contract.status = 'active'
    
    context = {
        'contracts': contracts,
        'super_admin': request.user,
        'current_date': current_date
    }
    return render(request, 'TriadApp/superadmin/contracts.html', context)

@superuser_required
def add_stall_contract(request):
    if request.method == 'POST':
        try:
            stall_id = request.POST.get('stall')
            stall = get_object_or_404(Stall, store_id=stall_id)
            current_date = timezone.now().date()
            
            # Check if stall already has an active contract
            existing_contract = StallContract.objects.filter(
                stall=stall,
                start_date__isnull=False  # Has started
            ).filter(
                Q(start_date__gt=current_date) |  # Future contract
                Q(start_date__lte=current_date, 
                  start_date__gt=current_date - timedelta(days=365))  # Active within 1 year
            ).first()
            
            if existing_contract:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This stall already has an active contract'
                })
            
            duration_months = 12  # Fixed to 1 year
            monthly_rate = Decimal('8000.00')  # Fixed rate
            
            # Create contract without start_date
            contract = StallContract.objects.create(
                stall=stall,
                duration_months=duration_months,
                monthly_rate=monthly_rate,
                payment_status='pending'
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Contract created successfully',
                'redirect_url': reverse('manage_contracts')
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
            
            amount = Decimal(request.POST.get('amount'))
            notes = request.POST.get('notes', '')
            
            # Calculate total amount and current total paid
            total_amount = contract.total_amount
            current_total_paid = sum(p.amount_paid for p in contract.payments.all())
            remaining_balance = total_amount - current_total_paid
            
            # Validate payment amount
            if amount > remaining_balance:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Payment amount exceeds remaining balance (₱{remaining_balance})'
                })
            
            # Create the payment
            payment = StallPayment.objects.create(
                contract=contract,
                amount_paid=amount,
                notes=notes
            )
            
            # Calculate new total paid after this payment
            new_total_paid = current_total_paid + amount
            
            # If this is the first payment, set the contract start date
            if not contract.start_date:
                contract.start_date = timezone.now().date()
                contract.save()
            
            # Check if fully paid
            if new_total_paid >= total_amount:
                # Activate the stall only when fully paid
                contract.stall.is_active = True
                contract.stall.save()
                contract.payment_status = 'paid'
                contract.save()
                message = 'Payment recorded successfully. Contract fully paid and stall activated!'
            else:
                # Keep stall inactive and update remaining balance
                contract.stall.is_active = False
                contract.stall.save()
                contract.payment_status = 'pending'
                contract.save()
                remaining = total_amount - new_total_paid
                message = f'Payment recorded successfully. Remaining balance: ₱{remaining:,.2f}'
            
            return JsonResponse({
                'status': 'success',
                'message': message,
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

# Add a new view to handle contract renewal
@superuser_required
def renew_contract(request, contract_id):
    if request.method == 'POST':
        try:
            old_contract = get_object_or_404(StallContract, id=contract_id)
            
            # Create new contract with fixed values
            new_contract = StallContract.objects.create(
                stall=old_contract.stall,
                duration_months=12,  # Fixed to 1 year
                monthly_rate=Decimal('8000.00'),  # Fixed rate of 8000
                payment_status='pending'
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Contract renewed successfully. Please make a payment to activate.',
                'redirect_url': reverse('manage_contracts')
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


