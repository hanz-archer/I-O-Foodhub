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
    # Automatically display all fields
    list_display = [field.name for field in AdminProfile._meta.fields]
