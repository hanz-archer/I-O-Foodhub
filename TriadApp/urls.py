
from django.urls import path
from . import views
from . import products
from . import accounts

urlpatterns = [
    path('', views.index, name='index'),
     path('admin-dashboard', views.admin, name='admin'),
     path('inventory', products.inventory, name='inventory'),
      path('superadmin_login', views.superadmin_login, name='superadmin_login'),
        path('admin_login', views.admin_login, name='admin_login'),
          path('employee_login', views.employee_login, name='employee_login'),
      path('super_admin', views.super_admin, name='super_admin'),

       path('register_admin', accounts.register_admin, name='register_admin'),
 
      path('add_stall', accounts.add_stall, name='add_stall'),
      path('delete_stall/<uuid:store_id>/', accounts.delete_stall, name='delete_stall'),
    path('edit_stall/', accounts.edit_stall, name='edit_stall'),
 
      path('add_product', products.add_product, name='add_product'),
]
        