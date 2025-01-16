from django.urls import path
from . import suoer_admin, views, products, stall_admins


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
   
    

    
    path('super_admin', views.super_admin, name='super_admin'),
    path('logout/', views.logout_view, name='logout'),
   path('clear-session/', views.clear_session, name='clear_session'),
   
    path('register_admin', suoer_admin.register_admin, name='register_admin'),
    path('add_stall', suoer_admin.add_stall, name='add_stall'),
    path('delete_stall/<uuid:store_id>/', suoer_admin.delete_stall, name='delete_stall'),
    path('edit_stall/', suoer_admin.edit_stall, name='edit_stall'),
    path('add_product', products.add_product, name='add_product'),
    path('edit_admin/', suoer_admin.edit_admin, name='edit_admin'),
    path('delete_admin/<int:admin_id>/', suoer_admin.delete_admin, name='delete_admin'),
    path('super-admin/profile/', suoer_admin.super_admin_profile, name='super_admin_profile'),
    path('super-admin/profile/update/', suoer_admin.update_super_admin_profile, name='update_super_admin_profile'),
    path('update_super_admin_profile/', suoer_admin.update_super_admin_profile, name='update_super_admin_profile'),

    path('stall-admin/dashboard/',  stall_admins.admin_dashboard, name='admin_dashboard'),
    path('stall-admin/login/', stall_admins.admin_login, name='admin_login'),
    path('manage_suppliers', stall_admins.manage_suppliers, name='manage_suppliers'),
    path('edit_supplier/<int:supplier_id>/', stall_admins.edit_supplier, name='edit_supplier'),
    path('delete_supplier/<int:supplier_id>/', stall_admins.delete_supplier, name='delete_supplier'),

    path('stall-admin/items/', stall_admins.item_management, name='item_management'),
    path('stall-admin/items/edit/<int:item_id>/', stall_admins.edit_item, name='edit_item'),
    path('stall-admin/items/delete/<int:item_id>/', stall_admins.delete_item, name='delete_item'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('send-contact/', views.send_contact, name='send_contact'),
 
]
        