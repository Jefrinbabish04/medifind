from django.urls import path
from . import views


urlpatterns = [
    path("login/", views.shop_login, name="shop_login"),
    path("logout/", views.shop_logout, name="shop_logout"),
    path("register/", views.shop_register, name="shop_register"),
    path("", views.dashboard, name="shop_dashboard"),
    path("inventory/", views.inventory_list, name="shop_inventory_list"),
    path("inventory/add/", views.inventory_create, name="shop_inventory_add"),
    path("inventory/<int:pk>/edit/", views.inventory_update, name="shop_inventory_edit"),
    path("inventory/<int:pk>/delete/", views.inventory_delete, name="shop_inventory_delete"),
    path("enquiries/", views.enquiry_list, name="shop_enquiry_list"),
    path("enquiries/<int:pk>/accept/", views.enquiry_accept, name="shop_enquiry_accept"),
    path("enquiries/<int:pk>/reject/", views.enquiry_reject, name="shop_enquiry_reject"),
]

