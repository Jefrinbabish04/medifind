from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path(
        'search/',
        views.search_medicine,
        name='search_medicine'
    ),

    path(
        'suggest/',
        views.medicine_suggest,
        name='medicine_suggest'
    ),

    path(
        'enquiry/<int:inventory_id>/',
        views.create_enquiry,
        name='create_enquiry'
    ),

    path(
        "customer/dashboard/",
        views.customer_dashboard,
        name="customer_dashboard",
    ),
]