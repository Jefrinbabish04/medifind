from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from api.models import MedicalShop, Inventory, Enquiry, Medicine
from .forms import ShopRegistrationForm, ShopLoginForm, InventoryForm, MedicineQuickCreateForm
from .models import ShopAccount
from .services import accept_enquiry_and_deduct_stock


def _get_shop_for_user(user):
    if not user.is_authenticated:
        return None
    try:
        return user.shop_account.shop
    except ShopAccount.DoesNotExist:
        return None


def shop_login(request):
    if request.user.is_authenticated and _get_shop_for_user(request.user):
        return redirect("shop_dashboard")

    if request.user.is_authenticated and _get_shop_for_user(request.user) is None:
        messages.warning(
            request,
            "This account is not linked to a medical shop. Log in with a shopkeeper account "
            "(demo: username abcp) or register your shop.",
        )
        logout(request)

    form = ShopLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            messages.error(request, "Invalid username or password.")
        elif _get_shop_for_user(user) is None:
            messages.error(
                request,
                "This user is not a shopkeeper. Use a shop account or register at /shop/register/.",
            )
        else:
            login(request, user)
            return redirect("shop_dashboard")

    return render(request, "shops/login.html", {"form": form})


def shop_logout(request):
    logout(request)
    return redirect("shop_login")


def shop_register(request):
    if request.user.is_authenticated and _get_shop_for_user(request.user):
        return redirect("shop_dashboard")

    form = ShopRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        from django.contrib.auth.models import User

        shop = MedicalShop.objects.create(
            name=form.cleaned_data["shop_name"],
            owner_name=form.cleaned_data["owner_name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data.get("email") or "",
            address=form.cleaned_data["address"],
            latitude=form.cleaned_data["latitude"],
            longitude=form.cleaned_data["longitude"],
            license_number=form.cleaned_data.get("license_number") or "",
        )
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        ShopAccount.objects.create(user=user, shop=shop)
        messages.success(request, "Shop registered successfully. Please login.")
        return redirect("shop_login")

    return render(request, "shops/register.html", {"form": form})


@login_required
def dashboard(request):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    inv_qs = Inventory.objects.filter(shop=shop).select_related("medicine")
    total_medicines = inv_qs.count()
    total_stock = inv_qs.aggregate(total=Sum("stock_quantity"))["total"] or 0

    enquiries = Enquiry.objects.filter(shop=shop)
    pending_count = enquiries.filter(status="pending").count()
    accepted_count = enquiries.filter(status="accepted").count()
    rejected_count = enquiries.filter(status="rejected").count()

    today = timezone.now().date()
    todays_activity = enquiries.filter(created_at__date=today).count()

    low_stock_threshold = 5
    low_stock_count = inv_qs.filter(stock_quantity__gt=0, stock_quantity__lte=low_stock_threshold).count()
    out_of_stock_count = inv_qs.filter(stock_quantity__lte=0).count()

    inv_chart = list(
        inv_qs.order_by("medicine__name")
        .values("medicine__name")
        .annotate(qty=Sum("stock_quantity"))
        .values_list("medicine__name", "qty")[:12]
    )

    enquiry_chart = [
        {"label": "Pending", "value": pending_count},
        {"label": "Accepted", "value": accepted_count},
        {"label": "Rejected", "value": rejected_count},
    ]

    return render(
        request,
        "shops/dashboard.html",
        {
            "shop": shop,
            "total_medicines": total_medicines,
            "total_stock": total_stock,
            "pending_count": pending_count,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "todays_activity": todays_activity,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "inv_chart": inv_chart,
            "enquiry_chart": enquiry_chart,
            "badge_pending": pending_count,
        },
    )


@login_required
def inventory_list(request):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    q = (request.GET.get("q") or "").strip()
    inv = Inventory.objects.filter(shop=shop).select_related("medicine").order_by("medicine__name")
    if q:
        inv = inv.filter(medicine__name__icontains=q)

    low_stock_threshold = 5
    return render(
        request,
        "shops/inventory_list.html",
        {"shop": shop, "inventory": inv, "q": q, "low_stock_threshold": low_stock_threshold, "badge_pending": Enquiry.objects.filter(shop=shop, status="pending").count()},
    )


@login_required
def inventory_create(request):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    form = InventoryForm(request.POST or None)
    med_form = MedicineQuickCreateForm(request.POST or None, prefix="med")

    if request.method == "POST":
        if "create_medicine" in request.POST and med_form.is_valid():
            med_form.save()
            messages.success(request, "Medicine added. You can now add it to inventory.")
            return redirect("shop_inventory_add")

        if "save_inventory" in request.POST and form.is_valid():
            obj = form.save(commit=False)
            obj.shop = shop
            obj.save()
            messages.success(request, "Inventory item added.")
            return redirect("shop_inventory_list")

    return render(
        request,
        "shops/inventory_form.html",
        {"shop": shop, "form": form, "med_form": med_form, "mode": "add", "badge_pending": Enquiry.objects.filter(shop=shop, status="pending").count()},
    )


@login_required
def inventory_update(request, pk):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    obj = get_object_or_404(Inventory, pk=pk, shop=shop)
    form = InventoryForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Inventory updated.")
        return redirect("shop_inventory_list")

    return render(
        request,
        "shops/inventory_form.html",
        {"shop": shop, "form": form, "mode": "edit", "badge_pending": Enquiry.objects.filter(shop=shop, status="pending").count()},
    )


@login_required
def inventory_delete(request, pk):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    obj = get_object_or_404(Inventory, pk=pk, shop=shop)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Inventory item deleted.")
        return redirect("shop_inventory_list")

    return render(
        request,
        "shops/inventory_delete.html",
        {"shop": shop, "inventory": obj, "badge_pending": Enquiry.objects.filter(shop=shop, status="pending").count()},
    )


@login_required
def enquiry_list(request):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    enquiries = Enquiry.objects.filter(shop=shop).order_by("-created_at")
    badge_pending = enquiries.filter(status="pending").count()
    return render(request, "shops/enquiries.html", {"shop": shop, "enquiries": enquiries, "badge_pending": badge_pending})


@login_required
def enquiry_accept(request, pk):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    enquiry = get_object_or_404(Enquiry, pk=pk, shop=shop)
    ok, msg = accept_enquiry_and_deduct_stock(enquiry)
    if ok:
        messages.success(request, msg)
    else:
        messages.warning(request, msg)
    return redirect("shop_enquiry_list")


@login_required
def enquiry_reject(request, pk):
    shop = _get_shop_for_user(request.user)
    if shop is None:
        messages.error(request, "Not a shopkeeper account. Please log in with your shop credentials.")
        return redirect("shop_login")

    enquiry = get_object_or_404(Enquiry, pk=pk, shop=shop)
    enquiry.status = "rejected"
    enquiry.save(update_fields=["status"])
    messages.error(request, "Enquiry rejected.")
    return redirect("shop_enquiry_list")
