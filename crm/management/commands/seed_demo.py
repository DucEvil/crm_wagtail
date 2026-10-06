from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Customer, Order


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho phần trình bày CRM"

    def handle(self, *args, **options):
        samples = [
            ("Nguyễn Minh Anh", "minhanh@example.com", "Công ty Sao Việt", "Website", Customer.Segment.POTENTIAL),
            ("Trần Quốc Bảo", "quocbao@example.com", "Nội thất An Phú", "Giới thiệu", Customer.Segment.VIP),
            ("Lê Thu Hà", "thuha@example.com", "Studio Mây", "Facebook", Customer.Segment.AT_RISK),
            ("Phạm Gia Huy", "giahuy@example.com", "Huy Logistics", "Sự kiện", Customer.Segment.POTENTIAL),
            ("Võ Ngọc Lan", "ngoclan@example.com", "Lan Beauty", "Instagram", Customer.Segment.NEW),
            ("Đỗ Hoàng Nam", "hoangnam@example.com", "Nam Tech", "Website", Customer.Segment.VIP),
            ("Bùi Khánh Linh", "khanhlinh@example.com", "Mộc Decor", "Giới thiệu", Customer.Segment.POTENTIAL),
            ("Huỳnh Đức Long", "duclong@example.com", "Long Foods", "Google", Customer.Segment.NEW),
            ("Đặng Thanh Mai", "thanhmai@example.com", "Mai Education", "Facebook", Customer.Segment.AT_RISK),
            ("Ngô Tuấn Kiệt", "tuankiet@example.com", "K-Tech", "Sự kiện", Customer.Segment.POTENTIAL),
        ]
        customers = []
        for index, (name, email, company, source, segment) in enumerate(samples):
            customer, _ = Customer.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "phone": f"090100000{index}",
                    "company": company,
                    "source": source,
                    "status": Customer.Status.ACTIVE,
                    "ai_segment": segment,
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
            (customers[4], "DH-1006", 850_000, 2),
            (customers[5], "DH-1007", 14_200_000, 35),
            (customers[5], "DH-1008", 9_600_000, 6),
            (customers[6], "DH-1009", 4_400_000, 48),
            (customers[6], "DH-1010", 2_900_000, 18),
            (customers[7], "DH-1011", 1_750_000, 1),
            (customers[8], "DH-1012", 3_300_000, 190),
            (customers[9], "DH-1013", 6_800_000, 72),
            (customers[9], "DH-1014", 8_100_000, 28),
            (customers[1], "DH-1015", 5_400_000, 92),
            (customers[3], "DH-1016", 3_700_000, 45),
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
