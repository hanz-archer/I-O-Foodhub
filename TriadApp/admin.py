from django.contrib import admin
from .models import (
    Stall, AdminProfile, CustomUser, Supplier, Supply,
    Item, ItemAddOn, ItemSupply, Category, LoginHistory
)

@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ('store_id', 'name', 'contact_number', 'is_active')
    search_fields = ('store_id', 'name')
    list_filter = ('is_active',)

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'username', 'email', 'stall')
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