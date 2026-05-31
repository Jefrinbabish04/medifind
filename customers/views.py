from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from api.models import Inventory, Enquiry, Medicine
from .forms import EnquiryForm
from .utils import haversine_km


def home(request):
    return render(request, 'customers/home.html')


@require_GET
def medicine_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})

    names = list(
        Medicine.objects.filter(name__istartswith=q)
        .order_by("name")
        .values_list("name", flat=True)[:8]
    )
    return JsonResponse({"results": names})


def search_medicine(request):

    query = request.GET.get('q')
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    results = []

    if query:

        results = (
            Inventory.objects.select_related("shop", "medicine")
            .filter(medicine__name__icontains=query, stock_quantity__gt=0)
        )

    user_lat = None
    user_lng = None
    try:
        if lat is not None and lng is not None:
            user_lat = float(lat)
            user_lng = float(lng)
            request.session["customer_lat"] = user_lat
            request.session["customer_lng"] = user_lng
    except (TypeError, ValueError):
        user_lat = None
        user_lng = None

    if user_lat is None or user_lng is None:
        user_lat = request.session.get("customer_lat")
        user_lng = request.session.get("customer_lng")

    rendered_results = []
    for inv in results:
        distance_km = None
        if user_lat is not None and user_lng is not None and inv.shop.latitude is not None and inv.shop.longitude is not None:
            try:
                distance_km = round(haversine_km(float(user_lat), float(user_lng), float(inv.shop.latitude), float(inv.shop.longitude)), 2)
            except (TypeError, ValueError):
                distance_km = None

        rendered_results.append(
            {
                "inventory": inv,
                "shop": inv.shop,
                "medicine": inv.medicine,
                "distance_km": distance_km,
                "navigate_url": f"https://www.google.com/maps/dir/?api=1&destination={inv.shop.latitude},{inv.shop.longitude}",
            }
        )

    context = {
        'query': query,
        'results': rendered_results,
        "has_location": user_lat is not None and user_lng is not None,
    }

    return render(
        request,
        'customers/search_results.html',
        context
    )



def create_enquiry(request, inventory_id):
    inv = get_object_or_404(Inventory.objects.select_related("shop", "medicine"), pk=inventory_id)

    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            enquiry = Enquiry.objects.create(
                shop=inv.shop,
                medicine=inv.medicine,
                medicine_name=inv.medicine.name,
                customer_name=form.cleaned_data["customer_name"],
                customer_phone=form.cleaned_data["customer_phone"],
                quantity=form.cleaned_data["quantity"],
                status="pending",
            )
            request.session["customer_phone"] = form.cleaned_data["customer_phone"]
            return redirect("customer_dashboard")
    else:
        form = EnquiryForm(
            initial={
                "customer_phone": request.session.get("customer_phone", ""),
                "quantity": 1,
            }
        )

    return render(
        request,
        "customers/enquiry_form.html",
        {"inventory": inv, "shop": inv.shop, "medicine": inv.medicine, "form": form},
    )


def customer_dashboard(request):
    customer_phone = request.session.get("customer_phone")
    enquiry_rows = []
    pending_count = accepted_count = rejected_count = 0

    if customer_phone:
        enquiries = (
            Enquiry.objects.select_related("shop", "medicine")
            .filter(customer_phone=customer_phone)
            .order_by("-created_at")
        )
        pending_count = enquiries.filter(status="pending").count()
        accepted_count = enquiries.filter(status="accepted").count()
        rejected_count = enquiries.filter(status="rejected").count()

        for e in enquiries:
            shop = e.shop
            navigate_url = (
                f"https://www.google.com/maps/dir/?api=1&destination={shop.latitude},{shop.longitude}"
            )
            enquiry_rows.append(
                {
                    "enquiry": e,
                    "navigate_url": navigate_url,
                    "show_navigate": e.status == "accepted",
                }
            )

    return render(
        request,
        "customers/dashboard.html",
        {
            "customer_phone": customer_phone,
            "enquiry_rows": enquiry_rows,
            "pending_count": pending_count,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
        },
    )