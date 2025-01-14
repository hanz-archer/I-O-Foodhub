from django.contrib import admin
from .models import Stall
from django.contrib.auth.models import AbstractUser
from django.utils.html import format_html
from django.db import models

from django.contrib import admin
from .models import AdminProfile


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
        'firstname',
        'middle_initial',
        'lastname',
        'age',
        'birthdate',
        'address',
        'contact_number',
        'get_store_id',
        'get_stall_name'
    )
    search_fields = ('username', 'firstname', 'lastname', 'contact_number')
    list_filter = ('stall', 'age', 'birthdate')
    ordering = ('username',)

    def get_store_id(self, obj):
        return obj.stall.store_id
    get_store_id.short_description = 'Store ID'

    def get_stall_name(self, obj):
        return obj.stall.name
    get_stall_name.short_description = 'Stall Name'