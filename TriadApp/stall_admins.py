from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AdminProfile, CustomUser, Supplier, Supply
from django.contrib.auth.hashers import check_password
from .decorators import admin_required
from .forms import SupplierForm
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import datetime, date
from django.views.decorators.http import require_http_methods
from .models import Category, Item, ItemAddOn, ItemSupply, Employee, TransactionReport
from decimal import Decimal, InvalidOperation
import json
import random
import string
from django.contrib import messages
from django.core.exceptions import ValidationError
import bcrypt

@admin_required
def admin_profile(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
    
        if request.method == 'POST':
            try:
                # Get form data
                firstname = request.POST.get('firstname')
                middle_initial = request.POST.get('middle_initial')
                lastname = request.POST.get('lastname')
                age = request.POST.get('age')
                birthdate = request.POST.get('birthdate')
                address = request.POST.get('address')
                email = request.POST.get('email')
                contact_number = request.POST.get('contact_number')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Validate required fields
                if not all([firstname, lastname, age, birthdate, address, contact_number]):
                    raise ValidationError('Please fill in all required fields.')
                
                # Update admin profile
                admin.firstname = firstname
                admin.middle_initial = middle_initial
                admin.lastname = lastname
                admin.age = age
                admin.birthdate = birthdate
                admin.address = address
                admin.email = email
                admin.contact_number = contact_number
                
                # Handle password change
                if new_password:
                    if new_password != confirm_password:
                        raise ValidationError('Passwords do not match.')
                    if len(new_password) < 8:
                        raise ValidationError('Password must be at least 8 characters long.')
                    
                    # Hash the new password
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
                    admin.password = hashed_password.decode('utf-8')
                
                admin.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile updated successfully!',
                    'password_changed': bool(new_password)
                }, status=200)
                
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'An error occurred while updating your profile.'
                }, status=500)
        
        return render(request, 'TriadApp/admin/admin_profile.html', {
            'admin': admin,
             'stall': admin.stall
        })
    except AdminProfile.DoesNotExist:
        return redirect('login')
    





@admin_required
def add_employee(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
    
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
                    
                    # Check if stall already has two employees
                    current_employee_count = Employee.objects.filter(stall=admin.stall, is_active=True).count()
                    if current_employee_count >= 2:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Maximum number of employees (2) reached for this stall.'
                        })
                    
                    # Get form data
                    data = {
                        'firstname': request.POST.get('firstname'),
                        'middle_initial': request.POST.get('middle_initial'),
                        'lastname': request.POST.get('lastname'),
                        'birthdate': request.POST.get('birthdate'),
                        'address': request.POST.get('address'),
                        'contact_number': request.POST.get('contact_number'),
                        'email': request.POST.get('email'),
                        'religion': request.POST.get('religion'),
                        'position': request.POST.get('position'),
                        'username': request.POST.get('username'),
                        'password': request.POST.get('password')
                    }
                    
                    # Validate username uniqueness across all user types
                    username = data['username']
                    email = data['email']
                    
                    # Check if email is provided (since it's optional)
                    if email:
                        # Check CustomUser (Superadmin)
                        if CustomUser.objects.filter(email=email).exists():
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Email already exists in the system.'
                            })
                        
                        # Check AdminProfile
                        if AdminProfile.objects.filter(email=email).exists():
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Email already exists in the system.'
                            })
                        
                        # Check Employee
                        if Employee.objects.filter(email=email).exists():
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Email already exists in the system.'
                            })
                    
                    # Check username across all user types
                    if CustomUser.objects.filter(username=username).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Username already exists in the system.'
                        })
                    
                    if AdminProfile.objects.filter(username=username).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Username already exists in the system.'
                        })
                    
                    if Employee.objects.filter(username=username).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Username already exists in the system.'
                        })
                    
                    # Validate required fields
                    required_fields = ['firstname', 'lastname', 'birthdate', 
                                    'address', 'contact_number', 'position', 
                                    'username', 'password']
                    
                    if not all(data[field] for field in required_fields):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Please fill in all required fields.'
                        })
                    
                    # Calculate age from birthdate
                    birthdate = date.fromisoformat(data['birthdate'])
                    today = date.today()
                    age = (today.year - birthdate.year - 
                          ((today.month, today.day) < (birthdate.month, birthdate.day)))
                    
                    # Validate age
                    if age < 15:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Employee must be at least 15 years old.'
                        })
                    
                    # Hash password
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
                    
                    # Print debug information
                    print(f"Raw Password: {data['password']}")
                    print(f"Hashed Password: {hashed_password.decode('utf-8')}")
                    
                    # Create employee with both passwords
                    employee = Employee(
                        stall=admin.stall,
                        firstname=data['firstname'],
                        middle_initial=data['middle_initial'],
                        lastname=data['lastname'],
                        age=age,
                        birthdate=birthdate,
                        address=data['address'],
                        contact_number=data['contact_number'],
                        email=data['email'],
                        religion=data['religion'],
                        position=data['position'],
                        username=data['username'],
                        password=hashed_password.decode('utf-8'),
                        raw_password=data['password']  # Store the raw password
                    )
                    
                    # Save the employee
                    employee.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Employee {employee.firstname} {employee.lastname} added successfully!'
                    })
                    
            except ValueError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid date format.'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
                
        # GET request - return form template
        employees = Employee.objects.filter(stall=admin.stall)
        return render(request, 'TriadApp/admin/employee_management.html', {
            'admin': admin,
            'employees': employees,
            'stall': admin.stall
        })
    
    except AdminProfile.DoesNotExist:
        return redirect('login')


@admin_required
def edit_employee(request, employee_id):
    try:
        admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
        employee = Employee.objects.get(id=employee_id, stall=admin.stall)
        
        if request.method == 'POST':
            # Get form data
            data = {
                'firstname': request.POST.get('firstname'),
                'middle_initial': request.POST.get('middle_initial'),
                'lastname': request.POST.get('lastname'),
                'birthdate': request.POST.get('birthdate'),
                'address': request.POST.get('address'),
                'contact_number': request.POST.get('contact_number'),
                'email': request.POST.get('email'),
                'religion': request.POST.get('religion'),
                'position': request.POST.get('position'),
                'username': request.POST.get('username'),
                'new_password': request.POST.get('new_password'),
                # Checkbox returns 'on' if checked, None if unchecked
                'is_active': request.POST.get('is_active') == 'on'
            }

            # Check if activating and if there's room for another active employee
            if data['is_active'] and not employee.is_active:
                current_active_count = Employee.objects.filter(
                    stall=admin.stall, 
                    is_active=True
                ).exclude(id=employee_id).count()
                
                if current_active_count >= 2:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Cannot activate employee. Maximum number of active employees (2) reached for this stall.'
                    })

            # Update employee data including status
            employee.is_active = data['is_active']
            
            # ... rest of your update logic ...

            employee.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Employee {employee.firstname} {employee.lastname} updated successfully!'
            })
            
        # GET request - return employee data
        return JsonResponse({
            'status': 'success',
            'employee': {
                'id': employee.id,
                'firstname': employee.firstname,
                'middle_initial': employee.middle_initial or '',
                'lastname': employee.lastname,
                'birthdate': employee.birthdate.isoformat() if employee.birthdate else '',
                'address': employee.address,
                'contact_number': employee.contact_number,
                'email': employee.email or '',
                'religion': employee.religion or '',
                'position': employee.position,
                'username': employee.username,
                'is_active': employee.is_active
            }
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Employee not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@admin_required
def delete_employee(request, employee_id):
    if request.method == 'POST':
        try:
            admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
            employee = Employee.objects.get(id=employee_id, stall=admin.stall)
            
            # Store name before deletion for success message
            employee_name = f"{employee.firstname} {employee.lastname}"
            
            # Delete the employee
            employee.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Employee {employee_name} has been deleted successfully.'
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Employee not found.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })




    

@admin_required
def manage_suppliers(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        today = date.today()
        
        if request.method == 'POST':
            # Create a mutable copy of POST data
            post_data = request.POST.copy()
            
            # Ensure all required fields are present
            required_fields = [
                'firstname', 'lastname', 'contact_person', 'license_number',
                'contact_number', 'email_address', 'address', 
                'contract_start_date', 'contract_end_date'
            ]
            
            # Check if all required fields are present
            missing_fields = [field for field in required_fields if not post_data.get(field)]
            if missing_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Required field missing: {missing_fields[0]}'
                })
            
            try:
                # Create new supplier instance
                supplier = Supplier(
                    stall=admin.stall,
                    firstname=post_data['firstname'],
                    middle_initial=post_data.get('middle_initial', ''),
                    lastname=post_data['lastname'],
                    contact_person=post_data['contact_person'],
                    license_number=post_data['license_number'],
                    contact_number=post_data['contact_number'],
                    email_address=post_data['email_address'],
                    address=post_data['address'],
                    contract_start_date=post_data['contract_start_date'],
                    contract_end_date=post_data['contract_end_date']
                )
                
                # Check if license number exists
                if Supplier.objects.filter(license_number=supplier.license_number).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'License number already exists!'
                    })
                
                # Validate and save
                supplier.full_clean()
                supplier.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Supplier added successfully!'
                })
                
            except ValidationError as e:
                error_message = str(e.message_dict[next(iter(e.message_dict))])
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # Rest of your view code for GET requests...
        suppliers = Supplier.objects.filter(stall=admin.stall)
        return render(request, 'TriadApp/admin/manage_suppliers.html', {
            'suppliers': suppliers,
            'admin': admin,
            'stall': admin.stall,
            'today': today
        })
        
    except AdminProfile.DoesNotExist:
        return redirect('login')
    except Exception as e:
        print("Unexpected Error:", str(e))
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        })
    



@admin_required
def edit_supplier(request, supplier_id):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
        
        if request.method == 'POST':
            # Create a mutable copy of POST data
            post_data = request.POST.copy()
            
            try:
                # Get the current and new license numbers
                current_license = supplier.license_number
                new_license = post_data.get('license_number', '').strip()
                
                # Print debug information
                print(f"Current license: {current_license}")
                print(f"New license: {new_license}")
                print(f"Are they equal? {current_license == new_license}")
                
                # Update the supplier fields
                supplier.firstname = post_data.get('firstname')
                supplier.middle_initial = post_data.get('middle_initial')
                supplier.lastname = post_data.get('lastname')
                supplier.contact_person = post_data.get('contact_person')
                supplier.contact_number = post_data.get('contact_number')
                supplier.email_address = post_data.get('email_address')
                supplier.address = post_data.get('address')
                supplier.contract_start_date = post_data.get('contract_start_date')
                supplier.contract_end_date = post_data.get('contract_end_date')
                
                # Only check license if it's actually different (case-insensitive comparison)
                if current_license.lower() != new_license.lower():
                    if Supplier.objects.exclude(id=supplier_id).filter(license_number__iexact=new_license).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'This license number is already registered to another supplier.'
                        })
                    supplier.license_number = new_license
                else:
                    # Keep the original license number
                    print("Keeping original license number")
                    supplier.license_number = current_license
                
                supplier.full_clean()  # Validate the model
                supplier.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Supplier information updated successfully!'
                })
                
            except ValidationError as e:
                print(f"Validation Error: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e.messages[0]) if hasattr(e, 'messages') else str(e)
                })
            except Exception as e:
                print(f"Exception: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # For GET request, return supplier data
        data = {
            'firstname': supplier.firstname,
            'middle_initial': supplier.middle_initial,
            'lastname': supplier.lastname,
            'contact_person': supplier.contact_person,
            'address': supplier.address,
            'contact_number': supplier.contact_number,
            'email_address': supplier.email_address,
            'license_number': supplier.license_number,
            'contract_start_date': supplier.contract_start_date.strftime('%Y-%m-%d'),
            'contract_end_date': supplier.contract_end_date.strftime('%Y-%m-%d'),
        }
        return JsonResponse(data)
        
    except AdminProfile.DoesNotExist:
        return redirect('login')
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        })


@admin_required
def delete_supplier(request, supplier_id):
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Supplier deleted successfully!'
        })
    except Supplier.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Supplier not found!'
        })
    




@admin_required
def manage_supplies(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        today = timezone.now().date()
        
        # Handle AJAX search request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('search'):
            search_query = request.GET.get('search')
            supplies = Supply.objects.filter(
                stall=admin.stall
            ).filter(
                Q(supply_id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(supplier__firstname__icontains=search_query) |
                Q(supplier__lastname__icontains=search_query)
            )
            
            supplies_data = [{
                'id': supply.id,
                'supply_id': supply.supply_id,
                'name': supply.name,
                'description': supply.description,
                'quantity': supply.quantity,
                'cost': str(supply.cost),
                'date_added': supply.date_added.strftime('%Y-%m-%d'),
                'expiration_date': supply.expiration_date.strftime('%Y-%m-%d') if supply.expiration_date else '',
                'status': supply.status,
                'supplier_name': f"{supply.supplier.firstname} {supply.supplier.lastname}"
            } for supply in supplies]
            
            return JsonResponse({
                'status': 'success',
                'supplies': supplies_data
            })
        
        if request.method == 'POST':
            try:
                # Get data from POST
                supply_id = request.POST.get('supply_id')
                name = request.POST.get('name')
                description = request.POST.get('description')
                quantity = request.POST.get('quantity', 0)
                cost = request.POST.get('cost')
                supplier_id = request.POST.get('supplier')
                date_added = request.POST.get('date_added', timezone.now().date().isoformat())
                expiration_date = request.POST.get('expiration_date')

                # Validation
                if not all([supply_id, name, cost, supplier_id, expiration_date]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please fill in all required fields including expiration date!'
                    })

                # Check if supply_id exists
                if Supply.objects.filter(stall=admin.stall, supply_id=supply_id).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Supply ID already exists!'
                    })

                # Get supplier instance
                try:
                    supplier = Supplier.objects.get(id=supplier_id, stall=admin.stall)
                    # Check if supplier contract is active
                    if supplier.contract_end_date < today:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Selected supplier\'s contract has expired!'
                        })
                except Supplier.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid supplier selected!'
                    })

                # Create supply
                supply = Supply.objects.create(
                    supply_id=supply_id,
                    name=name,
                    description=description,
                    quantity=quantity,
                    cost=cost,
                    supplier=supplier,
                    date_added=datetime.strptime(date_added, '%Y-%m-%d').date(),
                    expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date(),
                    stall=admin.stall
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Supply added successfully!'
                })

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        supplies = Supply.objects.filter(stall=admin.stall)
        # Only get active suppliers (contract not ended)
        active_suppliers = Supplier.objects.filter(
            stall=admin.stall,
            contract_end_date__gte=today
        )
        
        return render(request, 'TriadApp/admin/supply_management.html', {
            'supplies': supplies,
            'suppliers': active_suppliers,  # Pass only active suppliers
            'admin': admin,
            'stall': admin.stall
        })
    except AdminProfile.DoesNotExist:
        return redirect('login')
    



@admin_required
def edit_supply(request, supply_id):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        supply = get_object_or_404(Supply, id=supply_id, stall=admin.stall)
        
        if request.method == 'POST':
            try:
                name = request.POST.get('name')
                description = request.POST.get('description')
                quantity = request.POST.get('quantity', 0)
                cost = request.POST.get('cost')
                supplier_id = request.POST.get('supplier')
                date_added = request.POST.get('date_added')
                expiration_date = request.POST.get('expiration_date')
                
                if not expiration_date:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Expiration date is required!'
                    })
                
                # Get supplier instance
                supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
                
                # Update supply
                supply.name = name
                supply.description = description
                supply.quantity = quantity
                supply.cost = cost
                supply.supplier = supplier
                supply.date_added = datetime.strptime(date_added, '%Y-%m-%d').date()
                supply.expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
                supply.save()  # This will automatically update the status based on expiration date
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Supply updated successfully!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # For GET request, return supply data
        try:
            data = {
                'status': 'success',
                'data': {
                    'supply_id': supply.supply_id,
                    'name': supply.name,
                    'description': supply.description or '',
                    'quantity': supply.quantity,
                    'cost': str(supply.cost),
                    'supplier': supply.supplier.id,
                    'date_added': supply.date_added.strftime('%Y-%m-%d'),
                    'expiration_date': supply.expiration_date.strftime('%Y-%m-%d') if supply.expiration_date else '',
                    'status': supply.status
                }
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error loading supply data: {str(e)}'
            })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        })
    



@admin_required
@require_http_methods(["POST"])
def delete_supply(request, supply_id):
    try:
        admin_id = request.session.get('admin_id')
        if not admin_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            })
            
        admin = AdminProfile.objects.get(id=admin_id)
        supply = get_object_or_404(Supply, id=supply_id, stall=admin.stall)
        
        supply_name = supply.name  # Store name before deletion
        supply.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Supply "{supply_name}" deleted successfully!'
        })
        
    except AdminProfile.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Admin profile not found'
        })
    except Supply.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Supply not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error deleting supply: {str(e)}'
        })
    



@admin_required
def manage_categories(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        categories = Category.objects.filter(stall=admin.stall).order_by('name')
        
        return render(request, 'TriadApp/admin/manage_categories.html', {
            'categories': categories,
            'admin': admin,
             'stall': admin.stall
        })
    except AdminProfile.DoesNotExist:
        return redirect('login')

@admin_required
def add_category(request):
    if request.method == 'POST':
        try:
            admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
            name = request.POST.get('name')
            
            if Category.objects.filter(stall=admin.stall, name=name).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'A category with this name already exists'
                })
            
            category = Category.objects.create(
                stall=admin.stall,
                name=name
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Category added successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@admin_required
def edit_category(request, category_id):
    if request.method == 'POST':
        try:
            admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
            category = get_object_or_404(Category, id=category_id, stall=admin.stall)
            
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            # Check if another category with the same name exists
            if Category.objects.filter(stall=admin.stall, name=name).exclude(id=category_id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'A category with this name already exists'
                })
            
            category.name = name
            category.description = description
            category.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Category updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@admin_required
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
            category = get_object_or_404(Category, id=category_id, stall=admin.stall)
            category_name = category.name
            category.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Category "{category_name}" deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    





@admin_required
def manage_inventory(request):
    try:
        admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
        
        # Get only non-expired supplies
        valid_supplies = Supply.objects.filter(
            stall=admin.stall,
            status='good'  # Only get supplies with 'good' status
        )
        
        # Base queryset with prefetch_related, filtering for non-expired supplies
        items = Item.objects.filter(stall=admin.stall).prefetch_related(
            Prefetch('item_supplies',
                    queryset=ItemSupply.objects.filter(
                        supply__status='good'  # Only include non-expired supplies
                    ).select_related('supply')
            )
        )

        # Apply search if provided
        search_query = request.GET.get('search', '').strip()
        if search_query:
            items = items.filter(
                Q(item_id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Apply category filter if provided
        category_filter = request.GET.get('category', '').strip()
        if category_filter:
            items = items.filter(category__name=category_filter)
        
        categories = Category.objects.filter(stall=admin.stall)
        
        return render(request, 'TriadApp/admin/inventory_management.html', {
            'items': items,
            'categories': categories,
            'supplies': valid_supplies,  # Only pass non-expired supplies
            'admin': admin,
            'stall': admin.stall,
            'search_query': search_query,
            'category_filter': category_filter
        })
        
    except AdminProfile.DoesNotExist:
        return redirect('login')

@admin_required
def add_item(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
                
                # Generate auto-increment item_id
                last_item = Item.objects.filter(stall=admin.stall).order_by('-item_id').first()
                if last_item:
                    # Extract the numeric part and increment
                    try:
                        last_number = int(last_item.item_id[4:])  # Assuming format "ITEM1001"
                        new_number = last_number + 1
                    except ValueError:
                        new_number = 1001
                else:
                    new_number = 1001
                
                # Format new item_id
                item_id = f"ITEM{new_number}"
                
                # Get form data
                name = request.POST.get('name')
                category_id = request.POST.get('category')
                price = request.POST.get('price')
                item_quantity = request.POST.get('quantity', 0)
                size = request.POST.get('size') or None
                measurement = request.POST.get('measurement') or None
                expiration_date = request.POST.get('expiration_date') or None
                picture = request.FILES.get('picture')
                
                # Get category instance
                category = get_object_or_404(Category, id=category_id, stall=admin.stall)
                
                # Create item
                item = Item.objects.create(
                    item_id=item_id,  # Auto-generated item_id
                    stall=admin.stall,
                    name=name,
                    category=category,
                    price=price,
                    quantity=item_quantity,
                    size=size,
                    measurement=measurement,
                    expiration_date=expiration_date,
                    picture=picture
                )
                
                # Handle add-ons (name and price are required)
                addon_names = request.POST.getlist('addon_names[]')
                addon_prices = request.POST.getlist('addon_prices[]')
                
                for name, price in zip(addon_names, addon_prices):
                    if name and price:  # Both name and price must be provided
                        try:
                            addon_price = Decimal(str(price))
                            if addon_price <= 0:
                                raise ValidationError(f"Add-on price must be greater than 0 for {name}")
                            
                            ItemAddOn.objects.create(
                                item=item,
                                name=name,
                                price=addon_price
                            )
                        except (ValueError, InvalidOperation):
                            raise ValidationError(f"Invalid price value for add-on {name}")
                
                # Handle supplies from Supply model
                supply_ids = request.POST.getlist('supplies[]')
                supply_quantities = request.POST.getlist('supply_quantities[]')
                
                if not supply_ids or not supply_quantities:
                    raise ValidationError("At least one supply is required")
                
                for supply_id, quantity in zip(supply_ids, supply_quantities):
                    if supply_id and quantity:
                        try:
                            per_item_qty = Decimal(str(quantity))
                            if per_item_qty <= 0:
                                raise ValidationError("Supply quantity must be greater than 0")
                                
                            total_qty_needed = per_item_qty * Decimal(str(item_quantity))
                            
                            supply = get_object_or_404(Supply, 
                                                     id=supply_id, 
                                                     stall=admin.stall)
                            
                            # Check if enough supply quantity is available
                            if total_qty_needed > supply.quantity:
                                raise ValidationError(
                                    f"Insufficient quantity for supply {supply.name} ({supply.supply_id}). "
                                    f"Need {total_qty_needed} but only {supply.quantity} available."
                                )
                            
                            # Create the ItemSupply relationship
                            ItemSupply.objects.create(
                                item=item,
                                supply=supply,
                                quantity_per_item=per_item_qty
                            )
                            
                            # Update supply quantity
                            supply.quantity -= total_qty_needed
                            supply.save()
                            
                        except (ValueError, InvalidOperation):
                            raise ValidationError(f"Invalid quantity value for supply {supply.name}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Item added successfully',
                    'data': {
                        'id': item.id,
                        'item_id': item.item_id,
                        'name': item.name
                    }
                })
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })




@admin_required
def edit_item(request, item_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
                item = get_object_or_404(Item, id=item_id, stall=admin.stall)
                
                # Get form data for item
                item_name = request.POST.get('name')  # Changed variable name to item_name
                category_id = request.POST.get('category')
                price = request.POST.get('price')
                new_quantity = request.POST.get('quantity', 0)
                size = request.POST.get('size') or None
                measurement = request.POST.get('measurement') or None
                expiration_date = request.POST.get('expiration_date') or None
                picture = request.FILES.get('picture')
                
                # Get category instance
                category = get_object_or_404(Category, id=category_id, stall=admin.stall)
                
                # Handle supplies
                supply_ids = request.POST.getlist('supplies[]')
                supply_quantities = request.POST.getlist('supply_quantities[]')
                
                # Clear existing supplies
                item.item_supplies.all().delete()
                
                # Add new supplies
                for supply_id, quantity in zip(supply_ids, supply_quantities):
                    if supply_id and quantity:
                        try:
                            per_item_qty = Decimal(str(quantity))
                            if per_item_qty <= 0:
                                raise ValidationError("Supply quantity must be greater than 0")
                                
                            total_qty_needed = per_item_qty * Decimal(str(new_quantity))
                            
                            supply = get_object_or_404(Supply, 
                                                     id=supply_id, 
                                                     stall=admin.stall)
                            
                            if total_qty_needed > supply.quantity:
                                raise ValidationError(
                                    f"Insufficient quantity for supply {supply.name} ({supply.supply_id}). "
                                    f"Need {total_qty_needed} but only {supply.quantity} available."
                                )
                            
                            ItemSupply.objects.create(
                                item=item,
                                supply=supply,
                                quantity_per_item=per_item_qty
                            )
                            
                            supply.quantity -= total_qty_needed
                            supply.save()
                            
                        except (ValueError, InvalidOperation):
                            raise ValidationError(f"Invalid quantity value for supply {supply.name}")
                
                # Handle add-ons separately
                addon_names = request.POST.getlist('addon_names[]')
                addon_prices = request.POST.getlist('addon_prices[]')
                
                # Clear existing add-ons
                item.add_ons.all().delete()
                
                # Add new add-ons with their own names
                for addon_name, addon_price in zip(addon_names, addon_prices):
                    if addon_name and addon_price:
                        try:
                            addon_price_decimal = Decimal(str(addon_price))
                            if addon_price_decimal <= 0:
                                raise ValidationError(f"Add-on price must be greater than 0 for {addon_name}")
                            
                            ItemAddOn.objects.create(
                                item=item,
                                name=addon_name,
                                price=addon_price_decimal
                            )
                        except (ValueError, InvalidOperation):
                            raise ValidationError(f"Invalid price value for add-on {addon_name}")
                
                # Update item basic info separately from add-ons
                item.name = item_name  # Use the correct variable name
                item.category = category
                item.price = price
                item.quantity = new_quantity
                item.size = size
                item.measurement = measurement
                item.expiration_date = expiration_date
                if picture:
                    item.picture = picture
                item.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Item updated successfully'
                })
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    # GET request remains the same
    try:
        admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
        item = get_object_or_404(Item, id=item_id, stall=admin.stall)
        
        data = {
            'id': item.id,
            'item_id': item.item_id,
            'name': item.name,
            'category_id': item.category.id,
            'price': str(item.price),
            'quantity': str(item.quantity),
            'size': item.size or '',
            'measurement': item.measurement or '',
            'expiration_date': item.expiration_date.isoformat() if item.expiration_date else '',
            'picture_url': item.picture.url if item.picture else '',
            'supplies': [{
                'id': supply.supply.id,
                'quantity': str(supply.quantity_per_item)
            } for supply in item.item_supplies.all()],
            'add_ons': [{
                'name': addon.name,
                'price': str(addon.price)
            } for addon in item.add_ons.all()]
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
    

@admin_required
def delete_item(request, item_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
                item = get_object_or_404(Item, id=item_id, stall=admin.stall)
                
                # Return quantities back to supplies
                for supply_relation in item.item_supplies.all():
                    total_qty_to_return = supply_relation.quantity_per_item * item.quantity
                    supply = supply_relation.supply
                    supply.quantity += total_qty_to_return
                    supply.save()
                
                item_name = item.name
                
                # Delete the item's picture if it exists
                if item.picture:
                    try:
                        item.picture.delete()
                    except Exception as e:
                        print(f"Error deleting picture: {e}")
                
                # Delete item (this will cascade delete all relations)
                item.delete()
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Item "{item_name}" deleted successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })
    











@admin_required
def admin_reports(request):
    try:
        # Get the admin's profile
        admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
        
        # Get all reports from employees of this stall
        reports = TransactionReport.objects.filter(
            employee__stall=admin.stall
        ).select_related('employee').order_by('-submitted_at')
        
        context = {
            'reports': reports,
            'admin': admin,
            'stall': admin.stall
        }
        
        return render(request, 'TriadApp/admin/reports.html', context)
        
    except AdminProfile.DoesNotExist:
        return redirect('login')