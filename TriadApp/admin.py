from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Stall, AdminProfile, Supplier, Supply, LoginHistory, Category, Item, ItemProduct, ItemAddOn
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
from django import forms


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'middle_name', 
        'last_name', 
        'gender',
        'birthdate',
        'phone',
        'is_staff',
        'profile_image_preview'
    )
    
    list_filter = ('is_staff', 'is_superuser', 'gender', 'birthdate')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)

    # Add the custom fields to the fieldsets
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
                'email',
                'gender',
                'birthdate',
                'phone',
                'address',
                'profile_image'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Add the custom fields to the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'first_name',
                'middle_name',
                'last_name',
                'email',
                'gender',
                'birthdate',
                'phone',
                'address',
                'profile_image',
                'is_staff',
                'is_superuser'
            )
        }),
    )

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.profile_image.url)
        return "No Image"
    profile_image_preview.short_description = 'Profile Image'


@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'store_id', 'logo_preview', 'is_active')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = "Logo"


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'firstname',
        'middle_initial',
        'lastname',
        'age',
        'birthdate',
        'address',
        'contact_number',
        'get_store_id',
        'get_stall_name',
        'get_masked_password'
    )
    search_fields = ('username', 'email', 'firstname', 'lastname', 'contact_number')
    list_filter = ('stall', 'age', 'birthdate')
    ordering = ('username',)
    
    readonly_fields = ('get_masked_password',)
    
    fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password', 'get_masked_password')
        }),
        ('Personal Information', {
            'fields': ('firstname', 'middle_initial', 'lastname', 'email', 'age', 'birthdate', 'address')
        }),
        ('Contact Information', {
            'fields': ('contact_number',)
        }),
        ('Stall Assignment', {
            'fields': ('stall',)
        }),
    )

    def get_store_id(self, obj):
        return obj.stall.store_id
    get_store_id.short_description = 'Store ID'

    def get_stall_name(self, obj):
        return obj.stall.name
    get_stall_name.short_description = 'Stall Name'
    
    def get_masked_password(self, obj):
        """Display a masked version of the password hash for security"""
        if obj.password:
            return f"{obj.password[:8]}..."  # Show only first 8 characters
        return "No password set"
    get_masked_password.short_description = 'Password Hash'

    def save_model(self, request, obj, form, change):
        """Handle password hashing when saving through admin"""
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change) 

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'firstname',
        'middle_initial',
        'lastname',
        'contact_person',
        'license_number',
        'contact_number',
        'email_address',
        'contract_start_date',
        'contract_end_date',
        'stall'
    )
    
    list_filter = ('stall', 'contract_start_date', 'contract_end_date')
    search_fields = (
        'firstname', 
        'lastname', 
        'contact_person', 
        'license_number', 
        'email_address',
        'contact_number'
    )
    ordering = ('lastname', 'firstname')

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'firstname',
                'middle_initial',
                'lastname',
                'contact_person',
                'license_number',
            )
        }),
        ('Contact Information', {
            'fields': (
                'address',
                'contact_number',
                'email_address',
            )
        }),
        ('Contract Details', {
            'fields': (
                'stall',
                'contract_start_date',
                'contract_end_date',
            )
        }),
    ) 




@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = (
        'supply_id',
        'name',
        'description',
        'category',
        'quantity',
        'cost',
        'date_added',
        'stall_info',
        'supplier_info',
        'supplier_name',
        'created_at',
        'updated_at'
    )
    
    list_filter = (
        'category',
        'stall',
        'supplier',
        'date_added',
        'created_at'
    )
    
    search_fields = (
        'supply_id',
        'name',
        'description',
        'supplier_name',
        'stall__name',
        'supplier__firstname',
        'supplier__lastname'
    )
    
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'supply_id',
                'name',
                'description',
                'category'
            )
        }),
        ('Supply Details', {
            'fields': (
                'quantity',
                'cost',
                'date_added'
            )
        }),
        ('Relationships', {
            'fields': (
                'stall',
                'supplier',
                'supplier_name'
            )
        })
    )

    def stall_info(self, obj):
        return f"{obj.stall.name} ({obj.stall.store_id})"
    stall_info.short_description = 'Stall'
    stall_info.admin_order_field = 'stall__name'

    def supplier_info(self, obj):
        return f"{obj.supplier.firstname} {obj.supplier.lastname}"
    supplier_info.short_description = 'Supplier'
    supplier_info.admin_order_field = 'supplier__firstname'

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('username', 'login_time', 'status', 'ip_address', 'attempt_count', 
                   'is_blocked', 'system_details', 'wifi_connection')
    list_filter = ('status', 'is_blocked', 'login_time', 'operating_system')
    search_fields = ('username', 'ip_address', 'wifi_name')
    readonly_fields = ('login_time', 'user_agent', 'operating_system', 'os_version', 
                      'processor_info', 'gpu_info', 'wifi_name')
    
    def system_details(self, obj):
        return f"OS: {obj.operating_system} {obj.os_version}\nCPU: {obj.processor_info}\nGPU: {obj.gpu_info}"
    system_details.short_description = 'System Info'
    
    def wifi_connection(self, obj):
        return obj.wifi_name or 'Not Available'
    wifi_connection.short_description = 'WiFi Network'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'login_time', 'status', 'ip_address', 'attempt_count')
        }),
        ('Block Status', {
            'fields': ('is_blocked', 'block_expires')
        }),
        ('System Details', {
            'classes': ('collapse',),
            'fields': (
                'operating_system', 
                'os_version', 
                'processor_info', 
                'gpu_info',
                'wifi_name',
                'user_agent'
            )
        })
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    class Media:
        css = {
            'all': ('admin/css/system_info.css',)
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'stall', 'created_at', 'updated_at')
    list_filter = ('stall',)
    search_fields = ('name', 'stall__name')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'stall', 'category', 'price', 'quantity', 'is_available')
    list_filter = ('stall', 'category', 'is_available')
    search_fields = ('item_id', 'name', 'stall__name')
    readonly_fields = ('item_id', 'created_at', 'updated_at')
    ordering = ('stall', 'name')

@admin.register(ItemProduct)
class ItemProductAdmin(admin.ModelAdmin):
    list_display = ('item', 'supply', 'quantity_per_item')
    list_filter = ('item__stall', 'supply__category')
    search_fields = ('item__name', 'supply__name')
    raw_id_fields = ('item', 'supply')

@admin.register(ItemAddOn)
class ItemAddOnAdmin(admin.ModelAdmin):
    list_display = ('item', 'supply', 'quantity_per_item')
    list_filter = ('item__stall', 'supply__category')
    search_fields = ('item__name', 'supply__name')
    raw_id_fields = ('item', 'supply')