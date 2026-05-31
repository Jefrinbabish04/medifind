from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from api.models import MedicalShop, Medicine, Inventory
from shops.models import ShopAccount


class Command(BaseCommand):
    help = "Seed demo data for MediFind (ABC Medicals + Dolo 650)"

    def handle(self, *args, **options):
        shop, _ = MedicalShop.objects.get_or_create(
            name="ABC Medicals",
            defaults={
                "owner_name": "Owner",
                "phone": "9999999999",
                "email": "abcmedicals@example.com",
                "address": "12, Demo Street, Chennai",
                "latitude": 13.0827,
                "longitude": 80.2707,
                "license_number": "LIC-ABC-123",
            },
        )

        med, _ = Medicine.objects.get_or_create(
            name="Dolo 650",
            defaults={"brand": "Micro Labs", "category": "Tablet"},
        )

        inv, _ = Inventory.objects.get_or_create(
            shop=shop,
            medicine=med,
            defaults={"stock_quantity": 25, "price": "45.00"},
        )

        username = "abcp"
        password = "abcp1234"
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()

        ShopAccount.objects.get_or_create(user=user, shop=shop)

        self.stdout.write(self.style.SUCCESS("Seeded demo data successfully."))
        self.stdout.write(f"Shopkeeper login: username={username} password={password}")
        self.stdout.write(f"Try customer search: Dolo 650 (inventory stock={inv.stock_quantity})")

