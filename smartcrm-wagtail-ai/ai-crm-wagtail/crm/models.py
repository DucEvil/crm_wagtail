from django.db import models
from django.db.models import Sum
from wagtail.admin.panels import FieldPanel


class Customer(models.Model):
    class Status(models.TextChoices):
        LEAD = "lead", "Tiềm năng"
        ACTIVE = "active", "Đang hoạt động"
        INACTIVE = "inactive", "Ngừng hoạt động"

    class Segment(models.TextChoices):
        NEW = "new", "Khách hàng mới"
        POTENTIAL = "potential", "Khách hàng tiềm năng"
        VIP = "vip", "Khách hàng VIP"
        AT_RISK = "at_risk", "Có nguy cơ rời bỏ"
        UNCLASSIFIED = "unclassified", "Chưa phân loại"

    full_name = models.CharField("Họ và tên", max_length=160)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Số điện thoại", max_length=30, blank=True)
    company = models.CharField("Công ty", max_length=160, blank=True)
    status = models.CharField(
        "Trạng thái", max_length=20, choices=Status.choices, default=Status.LEAD
    )
    source = models.CharField("Nguồn khách hàng", max_length=120, blank=True)
    notes = models.TextField("Ghi chú", blank=True)
    ai_segment = models.CharField(
        "Phân khúc AI",
        max_length=24,
        choices=Segment.choices,
        default=Segment.UNCLASSIFIED,
    )
    ai_summary = models.TextField("Nhận định AI", blank=True)
    ai_email_suggestion = models.TextField("Email do AI gợi ý", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật", auto_now=True)

    panels = [
        FieldPanel("full_name"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("company"),
        FieldPanel("status"),
        FieldPanel("source"),
        FieldPanel("notes"),
        FieldPanel("ai_segment"),
        FieldPanel("ai_summary"),
        FieldPanel("ai_email_suggestion"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"

    def __str__(self):
        return self.full_name

    @property
    def total_spent(self):
        return self.orders.filter(status=Order.Status.COMPLETED).aggregate(total=Sum("total_amount"))["total"] or 0


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ xử lý"
        PROCESSING = "processing", "Đang xử lý"
        COMPLETED = "completed", "Hoàn thành"
        CANCELLED = "cancelled", "Đã hủy"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders", verbose_name="Khách hàng"
    )
    order_code = models.CharField("Mã đơn", max_length=40, unique=True)
    total_amount = models.DecimalField("Giá trị", max_digits=14, decimal_places=0)
    status = models.CharField(
        "Trạng thái", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    order_date = models.DateField("Ngày đặt hàng")
    notes = models.TextField("Ghi chú", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    panels = [
        FieldPanel("customer"),
        FieldPanel("order_code"),
        FieldPanel("total_amount"),
        FieldPanel("status"),
        FieldPanel("order_date"),
        FieldPanel("notes"),
    ]

    class Meta:
        ordering = ["-order_date", "-created_at"]
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

    def __str__(self):
        return f"{self.order_code} - {self.customer.full_name}"


class AIActionLog(models.Model):
    class Action(models.TextChoices):
        CLASSIFY = "classify", "Phân loại khách hàng"
        EMAIL = "email", "Gợi ý email"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="ai_logs", verbose_name="Khách hàng"
    )
    action_type = models.CharField("Tác vụ", max_length=20, choices=Action.choices)
    provider = models.CharField("Nhà cung cấp", max_length=40, default="mock")
    result = models.TextField("Kết quả")
    success = models.BooleanField("Thành công", default=True)
    created_at = models.DateTimeField("Thời gian", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Nhật ký AI"
        verbose_name_plural = "Nhật ký AI"

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.customer.full_name}"

# Create your models here.
