from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login
from .decorators import *

from django.shortcuts import redirect

from .models import Item, Employee, Category, ItemAddOn, Transaction, TransactionItem, TransactionItemAddOn, TransactionReport

from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.files.base import ContentFile
import csv
from io import StringIO







@employee_login_required
def employee_pos(request):
    employee_id = request.session.get('employee_id')
    
    try:
        employee = Employee.objects.get(id=employee_id)
        
        # Get items and categories for POS, filter by is_available instead of is_active
        items = Item.objects.filter(stall=employee.stall, is_available=True)
        categories = Category.objects.filter(stall=employee.stall)
        
        context = {
            'employee': employee,
            'stall': employee.stall,
            'items': items,
            'categories': categories,
        }
        return render(request, 'TriadApp/employee/pos.html', context)
    except Employee.DoesNotExist:
        return redirect('login')
    
@csrf_exempt
@employee_login_required
def process_order(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        cart_items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')
        date = data.get('date', timezone.now().date().isoformat())
        
        if not cart_items:
            return JsonResponse({'status': 'error', 'message': 'Cart is empty'})
        
        employee = Employee.objects.get(id=request.session.get('employee_id'))
        
        with transaction.atomic():
            # Calculate total amount
            total_amount = Decimal('0.00')
            for item in cart_items:
                # Get item specific to this stall
                item_obj = Item.objects.get(
                    item_id=item['id'],
                    stall=employee.stall  # Add stall filter
                )
                quantity = item['quantity']
                
                # Check stock availability
                if item_obj.quantity < quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient stock for {item_obj.name}'
                    })
                
                # Calculate item total with add-ons
                item_total = item_obj.price * quantity
                if 'addOns' in item:
                    for add_on in item['addOns']:
                        add_on_obj = ItemAddOn.objects.get(
                            id=add_on['id'],
                            item=item_obj  # Add item filter for add-ons
                        )
                        item_total += add_on_obj.price * add_on['quantity']
                
                total_amount += item_total
            
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                stall=employee.stall,
                employee=employee,
                payment_method=payment_method,
                total_amount=total_amount,
                date=date
            )
            
            # Process items and update inventory
            for item in cart_items:
                item_obj = Item.objects.get(
                    item_id=item['id'],
                    stall=employee.stall  # Add stall filter here too
                )
                quantity = item['quantity']
                
                # Create transaction item
                transaction_item = TransactionItem.objects.create(
                    transaction=transaction_obj,
                    item=item_obj,
                    quantity=quantity,
                    unit_price=item_obj.price,
                    subtotal=item_obj.price * quantity
                )
                
                # Process add-ons if any
                if 'addOns' in item:
                    for add_on in item['addOns']:
                        add_on_obj = ItemAddOn.objects.get(
                            id=add_on['id'],
                            item=item_obj  # Add item filter for add-ons
                        )
                        TransactionItemAddOn.objects.create(
                            transaction_item=transaction_item,
                            add_on=add_on_obj,
                            quantity=add_on['quantity'],
                            unit_price=add_on_obj.price,
                            subtotal=add_on_obj.price * add_on['quantity']
                        )
                
                # Update inventory
                item_obj.quantity -= quantity
                item_obj.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Order processed successfully',
                'transaction_id': transaction_obj.transaction_id
            })
            
    except Item.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Item not found or does not belong to your stall'
        })
    except ItemAddOn.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Add-on not found or does not belong to the item'
        })
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})

@employee_login_required
def get_item_addons(request, item_id):
    try:
        employee = Employee.objects.get(id=request.session.get('employee_id'))
        item = Item.objects.get(item_id=item_id, stall=employee.stall)
        addons = ItemAddOn.objects.filter(item=item)
        
        addon_list = [{
            'id': addon.id,
            'name': addon.name,
            'price': float(addon.price)
        } for addon in addons]
        
        return JsonResponse({
            'status': 'success',
            'addons': addon_list
        })
        
    except Item.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Item not found',
            'addons': []
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'addons': []
        })

@employee_login_required
def transaction_history(request):
    employee = Employee.objects.get(id=request.session.get('employee_id'))
    transaction_items = TransactionItem.objects.filter(
        transaction__stall=employee.stall
    ).select_related(
        'transaction',
        'item'
    ).prefetch_related(
        'add_ons',
        'add_ons__add_on'
    ).order_by('-transaction__date', '-transaction__created_at')

    # Calculate add-ons total for each transaction item
    for item in transaction_items:
        item.addons_total = sum(addon.subtotal for addon in item.add_ons.all())

    context = {
        'transaction_items': transaction_items,
        'employee': employee,
        'stall': employee.stall,
    }
    return render(request, 'TriadApp/employee/transaction.html', context)

@employee_login_required
def download_and_report_transactions(request):
    try:
        employee = Employee.objects.get(id=request.session.get('employee_id'))
        selected_ids = request.POST.getlist('transaction_ids[]') or []
        
        # Create CSV in memory
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Transaction ID', 'Date', 'Item Name', 'Size/Measurement', 'Quantity', 'Total Price'])
        
        # Get transactions based on selection
        transactions = TransactionItem.objects.filter(
            transaction__stall=employee.stall
        )
        
        if selected_ids:
            transactions = transactions.filter(transaction__id__in=selected_ids)
            
        transactions = transactions.select_related('transaction', 'item')
        
        if not transactions.exists():
            messages.error(request, 'No transactions selected')
            return redirect('employee_transactions')
        
        # Write transactions to CSV
        for item in transactions:
            writer.writerow([
                item.transaction.transaction_id,
                item.transaction.date.strftime('%Y-%m-%d'),
                item.item.name,
                item.item.size or item.item.measurement or '-',
                item.quantity,
                item.subtotal
            ])
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'transactions_{timestamp}.csv'
        
        # Get CSV content
        csv_content = csv_buffer.getvalue().encode('utf-8')
        
        # Create report and save file
        report = TransactionReport.objects.create(
            employee=employee,
            title=f'Transaction Report - {timestamp}',
            description=f'Automated transaction report for {len(selected_ids) or "all"} transactions generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        report.file.save(filename, ContentFile(csv_content))
        
        # Store report ID in session for pre-filling the form
        request.session['last_report_id'] = report.id
        
        # Create response for download
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Add success message
        messages.success(request, 'Report created and downloaded successfully!')
        
        # Return the download response
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('employee_transactions')

@employee_login_required
def submit_report(request):
    employee = Employee.objects.get(id=request.session.get('employee_id'))
    last_report = None
    last_report_id = request.session.get('last_report_id')
    
    if last_report_id:
        try:
            last_report = TransactionReport.objects.get(id=last_report_id)
            # Clear the session after retrieving
            del request.session['last_report_id']
        except TransactionReport.DoesNotExist:
            pass
    
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(id=request.session.get('employee_id'))
            
            # If editing existing report
            if request.POST.get('report_id'):
                report = TransactionReport.objects.get(id=request.POST.get('report_id'))
                report.title = request.POST.get('title')
                report.description = request.POST.get('description')
                if 'file' in request.FILES:
                    report.file = request.FILES.get('file')
                report.save()
            else:
                # Create new report
                report = TransactionReport.objects.create(
                    employee=employee,
                    title=request.POST.get('title'),
                    description=request.POST.get('description'),
                    file=request.FILES.get('file')
                )
            
            messages.success(request, 'Report submitted successfully!')
            return redirect('employee_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting report: {str(e)}')
            return redirect('submit_report')
    
    context = {
        'last_report': last_report,
        
           'employee': employee,
            'stall': employee.stall,
        
    }
    return render(request, 'TriadApp/employee/submit_report.html', context)

