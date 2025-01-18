from django.urls import path
from . import super_admin, views, stall_admins


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('clear-session/', views.clear_session, name='clear_session'),

    path('admin_dashboard',  views.admin_dashboard, name='admin_dashboard'),
    path('super_admin', views.super_admin, name='super_admin'),
   
   

    path('register_admin', super_admin.register_admin, name='register_admin'),
    path('add_stall', super_admin.add_stall, name='add_stall'),
    path('delete_stall/<uuid:store_id>/', super_admin.delete_stall, name='delete_stall'),
    path('edit_stall/', super_admin.edit_stall, name='edit_stall'),

    path('edit_admin/', super_admin.edit_admin, name='edit_admin'),
    path('delete_admin/<int:admin_id>/', super_admin.delete_admin, name='delete_admin'),
    path('super-admin/profile/', super_admin.super_admin_profile, name='super_admin_profile'),
    path('super-admin/profile/update/', super_admin.update_super_admin_profile, name='update_super_admin_profile'),
    path('update_super_admin_profile/', super_admin.update_super_admin_profile, name='update_super_admin_profile'),



    path('manage_suppliers', stall_admins.manage_suppliers, name='manage_suppliers'),
    path('edit_supplier/<int:supplier_id>/', stall_admins.edit_supplier, name='edit_supplier'),
    path('delete_supplier/<int:supplier_id>/', stall_admins.delete_supplier, name='delete_supplier'),

    path('manage_supplies', stall_admins.manage_supplies, name='manage_supplies'),
    path('stall-admin/supplies/edit/<int:supply_id>/', stall_admins.edit_supply, name='edit_supply'),
    path('stall-admin/supplies/delete/<int:supply_id>/', stall_admins.delete_supply, name='delete_supply'),


    path('stall-admin/categories/', stall_admins.manage_categories, name='manage_categories'),
    path('stall-admin/categories/add/', stall_admins.add_category, name='add_category'),
    path('stall-admin/categories/edit/<int:category_id>/', stall_admins.edit_category, name='edit_category'),
    path('stall-admin/categories/delete/<int:category_id>/', stall_admins.delete_category, name='delete_category'),
    
    path('stall-admin/profile/', stall_admins.admin_profile, name='admin_profile'),

    path('stall-admin/employees/add/', stall_admins.add_employee, name='add_employee'),
    path('stall-admin/employees/<int:employee_id>/edit/', stall_admins.edit_employee, name='edit_employee'),
    path('stall-admin/employees/<int:employee_id>/delete/', stall_admins.delete_employee, name='delete_employee'),


    path('stall-admin/inventory/', stall_admins.manage_inventory, name='manage_inventory'),
    path('stall-admin/items/add/', stall_admins.add_item, name='add_item'),
    path('stall-admin/items/delete/<int:item_id>/', stall_admins.delete_item, name='delete_item'),
    path('stall-admin/items/<int:item_id>/edit/', stall_admins.edit_item, name='edit_item'),

    
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('send-contact/', views.send_contact, name='send_contact'),

    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),

  



 
]
        