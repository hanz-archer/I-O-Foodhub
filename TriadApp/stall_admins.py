from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AdminProfile, CustomUser
from django.contrib.auth.hashers import check_password
from .decorators import admin_required
from .forms import SupplierForm
from .models import Supplier
from .models import Item, ItemSupply, Supplier, Stall, AdminProfile
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            admin_profile = AdminProfile.objects.get(username=username)
            if check_password(password, admin_profile.password):
                request.session['admin_id'] = admin_profile.id
                request.session['admin_name'] = f"{admin_profile.firstname} {admin_profile.lastname}"
                request.session['admin_id'] = admin_profile.id
                request.session['admin_name'] = f"{admin_profile.firstname} {admin_profile.lastname}"
                request.session['stall_id'] = str(admin_profile.stall.store_id)
                request.session['is_admin'] = True  # Flag to identify admin users
                
                return JsonResponse({
                    'success': True,
                    'message': f"Welcome, {admin_profile.firstname}!",
                    'redirect': reverse('admin_dashboard')
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




@admin_required
def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
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
    






    

@admin_required
def manage_suppliers(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        
        if request.method == 'POST':
            form = SupplierForm(request.POST)
            if form.is_valid():
                try:
                    supplier = form.save(commit=False)
                    supplier.stall = admin.stall
                    supplier.full_clean()  # Run model validation
                    supplier.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Supplier added successfully!'
                    })
                except ValidationError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e.messages[0])
                    })
                except IntegrityError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'License number already exists!'
                    })
            else:
                errors = dict(form.errors.items())
                return JsonResponse({
                    'status': 'error',
                    'message': list(errors.values())[0][0]
                })
        else:
            form = SupplierForm()
        
        suppliers = Supplier.objects.filter(stall=admin.stall)
        return render(request, 'TriadApp/admin/manage_suppliers.html', {
            'form': form,
            'suppliers': suppliers,
            'admin': admin,
            'stall': admin.stall
        })
    except AdminProfile.DoesNotExist:
        return redirect('login')
    




    

@admin_required
def edit_supplier(request, supplier_id):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
        
        if request.method == 'POST':
            form = SupplierForm(request.POST, instance=supplier)
            if form.is_valid():
                try:
                    supplier = form.save(commit=False)
                    supplier.stall = admin.stall
                    supplier.full_clean()
                    supplier.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Supplier updated successfully!'
                    })
                except ValidationError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e.messages[0])
                    })
                except IntegrityError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'License number already exists!'
                    })
            else:
                errors = dict(form.errors.items())
                return JsonResponse({
                    'status': 'error',
                    'message': list(errors.values())[0][0]
                })
        
        # For GET request, return supplier data
        data = {
            'firstname': supplier.firstname,
            'middle_initial': supplier.middle_initial,
            'lastname': supplier.lastname,
            'contact_person': supplier.contact_person,
            'license_number': supplier.license_number,
            'address': supplier.address,
            'contact_number': supplier.contact_number,
            'email_address': supplier.email_address,
            'contract_start_date': supplier.contract_start_date.strftime('%Y-%m-%d'),
            'contract_end_date': supplier.contract_end_date.strftime('%Y-%m-%d'),
        }
        return JsonResponse(data)
        
    except AdminProfile.DoesNotExist:
        return redirect('login')

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
def item_management(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        
        if request.method == 'POST':
            try:
                # Create the item
                item = Item.objects.create(
                    item_id=request.POST['itemId'],
                    name=request.POST['itemName'],
                    size=request.POST.get('size'),
                    measurement=request.POST.get('measurement'),
                    quantity=int(request.POST['quantity']),
                    cost=float(request.POST['cost']),
                    stall=admin.stall
                )

                # Create the supplies
                suppliers = request.POST.getlist('suppliers[]')
                names = request.POST.getlist('supplyNames[]')  # Changed from quantities

                for supplier_id, name in zip(suppliers, names):
                    supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
                    ItemSupply.objects.create(
                        item=item,
                        supplier=supplier,
                        name=name  # Changed from quantity
                    )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Item added successfully!',
                    'item': {
                        'id': item.id,
                        'item_id': item.item_id,
                        'name': item.name,
                        'size': item.size or "-",
                        'measurement': item.measurement or "-",
                        'quantity': item.quantity,
                        'cost': float(item.cost)
                    }
                })
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e.messages[0])
                })
            except IntegrityError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Item ID already exists!'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # GET request - display form and items
        items = Item.objects.filter(stall=admin.stall).order_by('-created_at')
        suppliers = Supplier.objects.filter(stall=admin.stall)
        
        return render(request, 'TriadApp/admin/item_management.html', {
            'items': items,
            'suppliers': suppliers,
            'admin': admin,
            'stall': admin.stall
        })
        
    except AdminProfile.DoesNotExist:
        return redirect('login')

@admin_required
def edit_item(request, item_id):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        item = get_object_or_404(Item, id=item_id, stall=admin.stall)
        
        if request.method == 'POST':
            try:
                # Update item details
                item.item_id = request.POST['itemId']
                item.name = request.POST['itemName']
                item.size = request.POST.get('size')
                item.measurement = request.POST.get('measurement')
                item.quantity = int(request.POST['quantity'])
                item.cost = float(request.POST['cost'])
                item.save()

                # Update supplies
                item.supplies.all().delete()  # Remove existing supplies
                suppliers = request.POST.getlist('suppliers[]')
                supply_names = request.POST.getlist('supplyNames[]')

                for supplier_id, name in zip(suppliers, supply_names):
                    supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
                    ItemSupply.objects.create(
                        item=item,
                        supplier=supplier,
                        name=name
                    )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Item updated successfully!'
                })
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e.messages[0])
                })
            except IntegrityError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Item ID already exists!'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        
        # For GET request, return item data
        supplies_data = [{
            'supplier_id': supply.supplier.id,
            'name': supply.name
        } for supply in item.supplies.all()]

        data = {
            'item_id': item.item_id,
            'name': item.name,
            'size': item.size or '',
            'measurement': item.measurement or '',
            'quantity': item.quantity,
            'cost': float(item.cost),
            'supplies': supplies_data
        }
        return JsonResponse(data)
        
    except AdminProfile.DoesNotExist:
        return redirect('login')

@admin_required
def delete_item(request, item_id):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        item = get_object_or_404(Item, id=item_id, stall=admin.stall)
        
        if request.method == 'POST':
            try:
                item_name = item.name
                item.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Item "{item_name}" has been deleted successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error deleting item: {str(e)}'
                })
        
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        })
        
    except AdminProfile.DoesNotExist:
        return redirect('login')
