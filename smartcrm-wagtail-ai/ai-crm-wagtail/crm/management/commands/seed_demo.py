from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Customer, Order


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho phần trình bày CRM"

    def handle(self, *args, **options):
        samples = [
            ("Nguyễn Minh Anh", "minhanh@example.com", "Công ty Sao Việt", "Website"),
            ("Trần Quốc Bảo", "quocbao@example.com", "Nội thất An Phú", "Giới thiệu"),
            ("Lê Thu Hà", "thuha@example.com", "Studio Mây", "Facebook"),
            ("Phạm Gia Huy", "giahuy@example.com", "Huy Logistics", "Sự kiện"),
        ]
        customers = []
        for index, (name, email, company, source) in enumerate(samples):
            customer, _ = Customer.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "phone": f"090100000{index}",
                    "company": company,
                    "source": source,
                    "status": Customer.Status.ACTIVE,
                    "notes": "Khách hàng mẫu phục vụ kiểm thử và thuyết trình.",
                },
            )
            customers.append(customer)

        order_rows = [
            (customers[0], "DH-1001", 2_500_000, 12),
            (customers[0], "DH-1002", 3_200_000, 3),
            (customers[1], "DH-1003", 22_000_000, 20),
            (customers[2], "DH-1004", 1_100_000, 150),
            (customers[3], "DH-1005", 7_800_000, 8),
        ]
        for customer, code, amount, days_ago in order_rows:
            Order.objects.get_or_create(
                order_code=code,
                defaults={
                    "customer": customer,
                    "total_amount": Decimal(amount),
                    "status": Order.Status.COMPLETED,
                    "order_date": timezone.localdate() - timedelta(days=days_ago),
                },
            )
        self.stdout.write(self.style.SUCCESS("Đã tạo dữ liệu mẫu."))
