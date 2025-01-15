from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Stall, AdminProfile, Supplier
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password

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