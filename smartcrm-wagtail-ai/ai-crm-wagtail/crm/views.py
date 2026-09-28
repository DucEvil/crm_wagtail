import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerForm, OrderForm
from .models import AIActionLog, Customer, Order
from .services.ai_service import classify_customer, suggest_email


@login_required
def dashboard(request):
    customers = Customer.objects.all()
    orders = Order.objects.all()
    segment_rows = list(
        customers.values("ai_segment").annotate(total=Count("id")).order_by("-total")
    )
    max_segment = max([row["total"] for row in segment_rows], default=1)
    segment_labels = dict(Customer.Segment.choices)
    for row in segment_rows:
        row["label"] = segment_labels[row["ai_segment"]]
        row["percent"] = round(row["total"] / max_segment * 100)

    context = {
        "customer_count": customers.count(),
        "active_count": customers.filter(status=Customer.Status.ACTIVE).count(),
        "order_count": orders.count(),
        "revenue": orders.filter(status=Order.Status.COMPLETED).aggregate(total=Sum("total_amount"))["total"] or 0,
        "recent_customers": customers[:6],
        "recent_orders": orders.select_related("customer")[:6],
        "segment_rows": segment_rows,
        "unclassified_count": customers.filter(ai_segment=Customer.Segment.UNCLASSIFIED).count(),
    }
    return render(request, "crm/dashboard.html", context)


@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    segment = request.GET.get("segment", "").strip()
    customers = Customer.objects.annotate(
        order_count=Count("orders"),
        spent=Sum("orders__total_amount", filter=Q(orders__status=Order.Status.COMPLETED)),
    )
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(company__icontains=query)
        )
    if segment:
        customers = customers.filter(ai_segment=segment)
    return render(
        request,
        "crm/customer_list.html",
        {
            "customers": customers,
            "query": query,
            "segment": segment,
            "segment_choices": Customer.Segment.choices,
        },
    )


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(
        request,
        "crm/customer_detail.html",
        {
            "customer": customer,
            "orders": customer.orders.all(),
            "ai_logs": customer.ai_logs.all()[:8],
        },
    )


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        messages.success(request, "Đã thêm khách hàng mới.")
        return redirect("crm:customer_detail", pk=customer.pk)
    return render(request, "crm/customer_form.html", {"form": form, "title": "Thêm khách hàng"})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật khách hàng.")
        return redirect("crm:customer_detail", pk=pk)
    return render(request, "crm/customer_form.html", {"form": form, "title": "Sửa khách hàng"})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Đã xóa khách hàng.")
        return redirect("crm:customer_list")
    return render(request, "crm/customer_confirm_delete.html", {"customer": customer})


@login_required
def order_create(request, customer_pk=None):
    initial = {"customer": customer_pk} if customer_pk else {}
    form = OrderForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        order = form.save()
        messages.success(request, "Đã tạo đơn hàng.")
        return redirect("crm:customer_detail", pk=order.customer_id)
    return render(request, "crm/order_form.html", {"form": form, "title": "Tạo đơn hàng"})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        order = form.save()
        messages.success(request, "Đã cập nhật đơn hàng.")
        return redirect("crm:customer_detail", pk=order.customer_id)
    return render(request, "crm/order_form.html", {"form": form, "title": "Sửa đơn hàng"})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    customer_id = order.customer_id
    if request.method == "POST":
        order.delete()
        messages.success(request, "Đã xóa đơn hàng.")
    return redirect("crm:customer_detail", pk=customer_id)


@login_required
def ai_classify(request, pk):
    if request.method != "POST":
        return redirect("crm:customer_detail", pk=pk)
    customer = get_object_or_404(Customer, pk=pk)
    try:
        result, provider = classify_customer(customer)
        customer.ai_segment = result["segment"]
        customer.ai_summary = f'{result["reason"]}\nĐề xuất: {result["recommended_action"]}'
        customer.save(update_fields=["ai_segment", "ai_summary", "updated_at"])
        AIActionLog.objects.create(
            customer=customer,
            action_type=AIActionLog.Action.CLASSIFY,
            provider=provider,
            result=json.dumps(result, ensure_ascii=False),
        )
        messages.success(request, f"AI đã phân loại: {customer.get_ai_segment_display()}.")
    except Exception as exc:
        AIActionLog.objects.create(
            customer=customer,
            action_type=AIActionLog.Action.CLASSIFY,
            provider="openai",
            result=str(exc),
            success=False,
        )
        messages.error(request, "Không thể phân loại lúc này. Hãy kiểm tra cấu hình AI.")
    return redirect("crm:customer_detail", pk=pk)


@login_required
def ai_email(request, pk):
    if request.method != "POST":
        return redirect("crm:customer_detail", pk=pk)
    customer = get_object_or_404(Customer, pk=pk)
    try:
        result, provider = suggest_email(customer)
        customer.ai_email_suggestion = result
        customer.save(update_fields=["ai_email_suggestion", "updated_at"])
        AIActionLog.objects.create(
            customer=customer,
            action_type=AIActionLog.Action.EMAIL,
            provider=provider,
            result=result,
        )
        messages.success(request, "AI đã tạo email gợi ý.")
    except Exception as exc:
        AIActionLog.objects.create(
            customer=customer,
            action_type=AIActionLog.Action.EMAIL,
            provider="openai",
            result=str(exc),
            success=False,
        )
        messages.error(request, "Không thể tạo email lúc này. Hãy kiểm tra cấu hình AI.")
    return redirect("crm:customer_detail", pk=pk)


def health(request):
    return HttpResponse("ok", content_type="text/plain")

# Create your views here.
