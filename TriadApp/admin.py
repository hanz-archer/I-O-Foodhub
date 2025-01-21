from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from .models import (
    Stall, AdminProfile, CustomUser, Supplier, Supply,
    Item, ItemAddOn, ItemSupply, Category, LoginHistory, Employee,
    Transaction, TransactionItem, TransactionItemAddOn, StallContract, StallPayment
)
from django.utils import timezone

@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ('store_id', 'name', 'contact_number', 'is_active')
    search_fields = ('store_id', 'name')
    list_filter = ('is_active',)

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'username', 'email', 'stall', 'password')
    search_fields = ('firstname', 'lastname', 'username', 'email')
    list_filter = ('stall',)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'gender', 'phone')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('gender', 'is_active', 'is_staff')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'stall', 'license_number', 'contact_number', 'email_address')
    search_fields = ('firstname', 'lastname', 'license_number', 'email_address')
    list_filter = ('stall', 'contract_start_date', 'contract_end_date')

@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('supply_id', 'name', 'stall', 'quantity', 'cost', 'supplier', 'date_added')
    search_fields = ('supply_id', 'name', 'supplier_name')
    list_filter = ('stall', 'supplier')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'stall', 'category', 'price', 'quantity', 'is_available')
    search_fields = ('item_id', 'name')
    list_filter = ('stall', 'category', 'is_available')

@admin.register(ItemAddOn)
class ItemAddOnAdmin(admin.ModelAdmin):
    list_display = ('item', 'name', 'price', 'created_at')
    search_fields = ('name', 'item__name')
    list_filter = ('item__stall',)

@admin.register(ItemSupply)
class ItemSupplyAdmin(admin.ModelAdmin):
    list_display = ('item', 'supply', 'quantity_per_item')
    search_fields = ('item__name', 'supply__name')
    list_filter = ('item__stall',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'stall', 'created_at')
    search_fields = ('name',)
    list_filter = ('stall',)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'ip_address',
        'login_time',
        'status',
        'is_blocked',
        'device_type',
        'operating_system',
        'browser'
    )
    
    list_filter = (
        'status',
        'is_blocked',
        'device_type',
        'operating_system',
        'browser',
        'login_time'
    )
    
    search_fields = (
        'username',
        'ip_address',
        'user_agent',
        'wifi_name',
        'operating_system',
        'browser'
    )
    
    readonly_fields = (
        'user',
        'admin_profile',
        'username',
        'ip_address',
        'login_time',
        'status',
        'user_agent',
        'attempt_count',
        'is_blocked',
        'block_expires',
        'operating_system',
        'os_version',
        'processor_info',
        'gpu_info',
        'browser',
        'device_type',
        'wifi_name'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'username',
                'user',
                'admin_profile',
                'login_time',
                'status',
                'ip_address'
            )
        }),
        ('Login Attempt Details', {
            'fields': (
                'attempt_count',
                'is_blocked',
                'block_expires'
            )
        }),
        ('System Information', {
            'fields': (
                'operating_system',
                'os_version',
                'processor_info',
                'gpu_info',
                'browser',
                'device_type',
                'wifi_name'
            )
        }),
        ('Raw Data', {
            'classes': ('collapse',),
            'fields': ('user_agent',)
        })
    )
    
    ordering = ('-login_time',)
    date_hierarchy = 'login_time'
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'firstname', 
        'middle_initial', 
        'lastname', 
        'age', 
        'birthdate', 
        'position', 
        'contact_number', 
        'email',
        'is_active',
        'date_hired',
        'username',
        'raw_password',
        'stall'
    )
    
    list_filter = (
        'is_active', 
        'position', 
        'date_hired',
        'stall'
    )
    
    search_fields = (
        'firstname',
        'lastname',
        'username',
        'position',
        'contact_number',
        'email'
    )
    
    readonly_fields = ('date_hired', 'age')
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'firstname',
                'middle_initial',
                'lastname',
                'birthdate',
                'age',
                'religion',
                'address',
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_number',
                'email',
            )
        }),
        ('Employment Details', {
            'fields': (
                'stall',
                'position',
                'date_hired',
                'is_active'
            )
        }),
        ('Account Information', {
            'fields': (
                'username',
                'password',
                'raw_password'
            )
        }),
    )
    
    ordering = ('lastname', 'firstname')
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        """Save both encrypted and raw password"""
        if not change:  # If this is a new object
            obj.raw_password = form.cleaned_data.get('password', '')
            
        elif 'password' in form.changed_data:  # If password was changed
            obj.raw_password = form.cleaned_data.get('password', '')
            
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields
    
    
    
        return ('date_hired', 'age')

class TransactionItemAddOnInline(admin.TabularInline):
    model = TransactionItemAddOn
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('add_on', 'quantity', 'unit_price', 'subtotal')
    can_delete = False

class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('item', 'quantity', 'unit_price', 'subtotal')
    can_delete = False

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'stall', 'employee', 'get_items_display', 
                   'payment_method', 'total_amount', 'date', 'created_at')
    list_filter = ('stall', 'payment_method', 'date', 'created_at', 'employee')
    search_fields = ('transaction_id', 'stall__name', 'employee__user__username', 
                    'items__item__name')
    readonly_fields = ('transaction_id', 'created_at', 'get_items_detail')
    inlines = [TransactionItemInline]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'stall', 'employee', 'date')
        }),
        ('Items Information', {
            'fields': ('get_items_detail',)
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def get_items_display(self, obj):
        items = obj.items.all()
        return ", ".join([f"{item.item.name} (x{item.quantity})" for item in items])
    get_items_display.short_description = 'Items'

    def get_items_detail(self, obj):
        items = obj.items.all()
        details = []
        for item in items:
            # Calculate item total including add-ons
            item_total = item.subtotal
            item_detail = f"• {item.item.name}\n"
            item_detail += f"  Quantity: {item.quantity}\n"
            item_detail += f"  Unit Price: ₱{item.unit_price}\n"
            
            # Add add-ons if any
            addons = item.add_ons.all()
            if addons:
                item_detail += "  Add-ons:\n"
                for addon in addons:
                    item_detail += f"    - {addon.add_on.name} x{addon.quantity} @ ₱{addon.unit_price} = ₱{addon.subtotal}\n"
                    item_total += addon.subtotal
            
            item_detail += f"  Total: ₱{item_total}\n"
            details.append(item_detail)
        
        return "\n".join(details)
    get_items_detail.short_description = 'Items Detail'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('stall', 'employee', 'total_amount', 'date')
        return self.readonly_fields

@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'item', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('transaction__stall', 'item__category')
    search_fields = ('transaction__transaction_id', 'item__name')
    readonly_fields = ('subtotal',)
    inlines = [TransactionItemAddOnInline]

@admin.register(TransactionItemAddOn)
class TransactionItemAddOnAdmin(admin.ModelAdmin):
    list_display = ('transaction_item', 'add_on', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('transaction_item__transaction__stall',)
    search_fields = ('transaction_item__transaction__transaction_id', 'add_on__name')
    readonly_fields = ('subtotal',)
    
    fieldsets = (
        ('Transaction Item Information', {
            'fields': ('transaction_item',)
        }),
        ('Add-on Details', {
            'fields': ('add_on', 'quantity', 'unit_price', 'subtotal')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('transaction_item', 'add_on', 'unit_price')
        return self.readonly_fields

class StallPaymentInline(admin.TabularInline):
    model = StallPayment
    extra = 0
    readonly_fields = ('receipt_number', 'created_at')

@admin.register(StallContract)
class StallContractAdmin(admin.ModelAdmin):
    list_display = ('stall', 'start_date', 'end_date', 'monthly_rate', 
                   'payment_status', 'get_total_paid', 'is_active')
    list_filter = ('payment_status', 'duration_months', 'start_date')
    search_fields = ('stall__name',)
    inlines = [StallPaymentInline]
    
    def get_total_paid(self, obj):
        return sum(payment.amount_paid for payment in obj.payments.all())
    get_total_paid.short_description = 'Total Paid'
    
    def is_active(self, obj):
        return obj.end_date >= timezone.now().date() and obj.payment_status == 'paid'
    is_active.boolean = True
    is_active.short_description = 'Active'

@admin.register(StallPayment)
class StallPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number',
        'contract',
        'payment_date',
        'amount_paid',
    ]
    
    list_filter = [
        'payment_date',
        'contract',
    ]
    
    search_fields = [
        'receipt_number',
        'contract__stall__name',
        'notes',
    ]
    
    readonly_fields = ['receipt_number', 'payment_date']
    



    