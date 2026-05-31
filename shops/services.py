from django.db import transaction

from api.models import Inventory, Enquiry


def accept_enquiry_and_deduct_stock(enquiry: Enquiry) -> tuple[bool, str]:
    """
    Mark enquiry accepted and reduce shop inventory by enquiry.quantity.
    Returns (success, message). Only processes pending enquiries once.
    """
    if enquiry.status != "pending":
        return False, "This enquiry was already processed."

    with transaction.atomic():
        enquiry = Enquiry.objects.select_for_update().get(pk=enquiry.pk)

        if enquiry.status != "pending":
            return False, "This enquiry was already processed."

        inv = None
        if enquiry.medicine_id:
            inv = (
                Inventory.objects.select_for_update()
                .filter(shop=enquiry.shop_id, medicine=enquiry.medicine_id)
                .first()
            )
        if inv is None:
            inv = (
                Inventory.objects.select_for_update()
                .filter(shop=enquiry.shop_id, medicine__name__iexact=enquiry.medicine_name)
                .first()
            )

        if inv is None:
            enquiry.status = "accepted"
            enquiry.save(update_fields=["status"])
            return True, "Enquiry accepted (inventory record not found; stock not updated)."

        qty = enquiry.quantity
        if inv.stock_quantity < qty:
            deducted = inv.stock_quantity
            inv.stock_quantity = 0
            inv.save(update_fields=["stock_quantity"])
            enquiry.status = "accepted"
            enquiry.save(update_fields=["status"])
            return (
                True,
                f"Enquiry accepted. Stock updated: deducted {deducted} (requested {qty}; insufficient stock).",
            )

        inv.stock_quantity -= qty
        inv.save(update_fields=["stock_quantity"])
        enquiry.status = "accepted"
        enquiry.save(update_fields=["status"])
        return True, f"Enquiry accepted. Stock reduced by {qty} (remaining: {inv.stock_quantity})."
