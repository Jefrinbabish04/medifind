from django.db import models
from django.contrib.auth.models import User
from api.models import MedicalShop

class ShopAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shop_account")
    shop = models.OneToOneField(MedicalShop, on_delete=models.CASCADE, related_name="account")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop.name} ({self.user.username})"
