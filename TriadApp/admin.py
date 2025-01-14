from django.contrib import admin
from .models import Stall

from django.utils.html import format_html

@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'store_id', 'logo_preview')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = "Logo"

