from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from .models import (
    Stall, AdminProfile, CustomUser, Supplier, Supply,
    Item, ItemAddOn, ItemSupply, Category, LoginHistory, Employee,
    Transaction, TransactionItem, TransactionItemAddOn, StallContract, StallPayment
)
from django.utils import timezone



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
