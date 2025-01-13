
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
     path('admin', views.admin, name='admin'),
     path('inventory', views.inventory, name='inventory'),
  path('login', views.login, name='login'),
      path('superadmin', views.superadmin, name='superadmin'),
 
      path('add_product', views.add_product, name='add_product'),
]
        