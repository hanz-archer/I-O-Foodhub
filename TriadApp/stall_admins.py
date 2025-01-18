from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AdminProfile, CustomUser
from django.contrib.auth.hashers import check_password
from .decorators import admin_required
from .forms import SupplierForm
from .models import Supplier
from .models import Supplier, Supply, AdminProfile
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.views.decorators.http import require_http_methods
from .models import Category
from .models import Item, ItemAddOn, ItemSupply
from decimal import Decimal, InvalidOperation
import json
import random
import string






    






    

@admin_required
def manage_suppliers(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('login')
    
    try:
        admin = AdminProfile.objects.get(id=admin_id)
        
        # Handle AJAX search request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('search'):
            search_query = request.GET.get('search')
            suppliers = Supplier.objects.filter(
                stall=admin.stall
            ).filter(
                Q(firstname__icontains=search_query) |
                Q(lastname__icontains=search_query) |
                Q(license_number__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(email_address__icontains=search_query)
            )
            
            suppliers_data = [{
                'id': supplier.id,
                'firstname': supplier.firstname,
                'middle_initial': supplier.middle_initial,
                'lastname': supplier.lastname,
                'license_number': supplier.license_number,
                'contact_person': supplier.contact_person,
                'contact_number': supplier.contact_number,
                'email_address': supplier.email_address,
                'contract_start_date': supplier.contract_start_date.strftime('%Y-%m-%d') if supplier.contract_start_date else '',
                'contract_end_date': supplier.contract_end_date.strftime('%Y-%m-%d') if supplier.contract_end_date else ''
            } for supplier in suppliers]
            
            return JsonResponse({
                'status': 'success',
                'suppliers': suppliers_data
            })
        
        if request.method == 'POST':
            form = SupplierForm(request.POST)
            if form.is_valid():
                try:
                    # Check if license number exists
                    license_number = form.cleaned_data['license_number']
                    if Supplier.objects.filter(stall=admin.stall, license_number=license_number).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'License number already exists!'
                        })
                    
                    supplier = form.save(commit=False)
                    supplier.stall = admin.stall
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
                    # Get the submitted license number
                    new_license = form.cleaned_data['license_number']
                    
                    # Check if it's different from the original
                    if new_license != supplier.license_number:
                        # Check if this license exists for any other supplier
                        if Supplier.objects.filter(license_number=new_license).exclude(id=supplier_id).exists():
                            return JsonResponse({
                                'status': 'error',
                                'message': 'This license number is already registered to another supplier.'
                            })
                    
                    supplier = form.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Supplier information updated successfully!'
                    })
                except ValidationError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e.messages[0])
                    })
                except IntegrityError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This license number is already registered to another supplier.'
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

                # Validation
                if not all([supply_id, name, cost, supplier_id]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please fill in all required fields!'
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
                except Supplier.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid supplier selected!'
                    })

                # Create supply without category
                supply = Supply.objects.create(
                    supply_id=supply_id,
                    name=name,
                    description=description,
                    quantity=quantity,
                    cost=cost,
                    supplier=supplier,
                    date_added=datetime.strptime(date_added, '%Y-%m-%d').date(),
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
        suppliers = Supplier.objects.filter(stall=admin.stall)  # For supplier dropdown
        return render(request, 'TriadApp/admin/supply_management.html', {
            'supplies': supplies,
            'suppliers': suppliers,
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
                
                # Get supplier instance
                supplier = get_object_or_404(Supplier, id=supplier_id, stall=admin.stall)
                
                # Update supply
                supply.name = name
                supply.description = description
                supply.quantity = quantity
                supply.cost = cost
                supply.supplier = supplier
                supply.date_added = datetime.strptime(date_added, '%Y-%m-%d').date()
                supply.save()
                
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
                }
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error loading supply data: {str(e)}'
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
        
        # Handle AJAX request first
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.method == 'POST':
                return add_item(request)
        
        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        category_filter = request.GET.get('category', '').strip()
        
        # Base queryset
        items = Item.objects.filter(stall=admin.stall)
        
        # Apply search if provided
        if search_query:
            items = items.filter(
                Q(item_id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Apply category filter if provided
        if category_filter:
            items = items.filter(category__name=category_filter)
        
        categories = Category.objects.filter(stall=admin.stall)
        supplies = Supply.objects.filter(stall=admin.stall)
        
        return render(request, 'TriadApp/admin/inventory_management.html', {
            'items': items,
            'categories': categories,
            'supplies': supplies,
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
                
                # Get form data
                item_id = request.POST.get('item_id')
                name = request.POST.get('name')
                category_id = request.POST.get('category')
                price = request.POST.get('price')
                item_quantity = request.POST.get('quantity', 0)
                size = request.POST.get('size') or None
                measurement = request.POST.get('measurement') or None
                expiration_date = request.POST.get('expiration_date') or None
                picture = request.FILES.get('picture')
                
                # Check if item_id is unique
                if Item.objects.filter(item_id=item_id).exists():
                    raise ValidationError("Item ID already exists. Please use a different ID.")
                
                # Get category instance
                category = get_object_or_404(Category, id=category_id, stall=admin.stall)
                
                # Create item
                item = Item.objects.create(
                    item_id=item_id,
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
def edit_item(request, item_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                admin = AdminProfile.objects.get(id=request.session.get('admin_id'))
                item = get_object_or_404(Item, id=item_id, stall=admin.stall)
                
                # Get form data
                name = request.POST.get('name')
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
                
                # Handle add-ons
                addon_names = request.POST.getlist('addon_names[]')
                addon_prices = request.POST.getlist('addon_prices[]')
                
                # Clear existing add-ons
                item.add_ons.all().delete()
                
                # Add new add-ons
                for name, price in zip(addon_names, addon_prices):
                    if name and price:
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
                
                # Update item basic info
                item.name = name
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
    
    # GET request - return item data for editing
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
    



