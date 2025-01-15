from django.urls import path
from . import views, accounts, products, stall_admins


urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_page, name='login'),
   
    
    path('superadmin_login', views.superadmin_login, name='superadmin_login'),
    path('admin_login', views.admin_login, name='admin_login'),
    path('employee_login', views.employee_login, name='employee_login'),

    
    path('super_admin', views.super_admin, name='super_admin'),
    path('logout/', views.logout_view, name='logout'),

    path('register_admin', accounts.register_admin, name='register_admin'),
    path('add_stall', accounts.add_stall, name='add_stall'),
    path('delete_stall/<uuid:store_id>/', accounts.delete_stall, name='delete_stall'),
    path('edit_stall/', accounts.edit_stall, name='edit_stall'),
    path('add_product', products.add_product, name='add_product'),
    path('edit_admin/', accounts.edit_admin, name='edit_admin'),
    path('delete_admin/<int:admin_id>/', accounts.delete_admin, name='delete_admin'),
    path('super-admin/profile/', accounts.super_admin_profile, name='super_admin_profile'),
    path('super-admin/profile/update/', accounts.update_super_admin_profile, name='update_super_admin_profile'),
    path('update_super_admin_profile/', accounts.update_super_admin_profile, name='update_super_admin_profile'),

    path('stall-admin/dashboard/',  stall_admins.admin_dashboard, name='admin_dashboard'),
    path('stall-admin/login/', stall_admins.admin_login, name='admin_login'),
    path('manage_suppliers', stall_admins.manage_suppliers, name='manage_suppliers'),
    path('edit_supplier/<int:supplier_id>/', stall_admins.edit_supplier, name='edit_supplier'),
    path('delete_supplier/<int:supplier_id>/', stall_admins.delete_supplier, name='delete_supplier'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
        