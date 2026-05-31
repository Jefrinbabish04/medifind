from django.contrib import admin

from .models import ShopAccount


@admin.register(ShopAccount)
class ShopAccountAdmin(admin.ModelAdmin):
    list_display = ("shop", "user", "created_at")
    search_fields = ("shop__name", "user__username")
