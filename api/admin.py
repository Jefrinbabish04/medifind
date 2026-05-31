from django.contrib import admin

from .models import MedicalShop, Medicine, Inventory, Enquiry


class InventoryInline(admin.TabularInline):
    model = Inventory
    extra = 0
    autocomplete_fields = ["medicine"]
    fields = ("medicine", "stock_quantity", "price", "expiry_date")


@admin.register(MedicalShop)
class MedicalShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_name", "phone", "email", "license_number", "created_at")
    search_fields = ("name", "owner_name", "phone", "email", "license_number", "address")
    list_filter = ("created_at",)
    inlines = [InventoryInline]


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category")
    search_fields = ("name", "brand", "category")
    ordering = ("name",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("shop", "medicine", "stock_quantity", "price", "expiry_date")
    search_fields = ("shop__name", "medicine__name", "medicine__brand")
    list_filter = ("shop", "expiry_date")
    autocomplete_fields = ["shop", "medicine"]


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("shop", "medicine_name", "customer_name", "customer_phone", "quantity", "status", "created_at")
    search_fields = ("shop__name", "medicine_name", "customer_name", "customer_phone")
    list_filter = ("status", "created_at", "shop")
    ordering = ("-created_at",)
    autocomplete_fields = ["shop", "medicine"]
