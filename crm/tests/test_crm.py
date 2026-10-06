from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from crm.models import AIActionLog, Customer, Order
from crm.services.ai_service import classify_customer, suggest_email


class CRMBaseTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("tester", password="safe-test-password")
        self.customer = Customer.objects.create(
            full_name="Nguyễn An",
            email="an@example.com",
            status=Customer.Status.ACTIVE,
        )


class ModelTests(CRMBaseTest):
    def test_customer_total_spent(self):
        Order.objects.create(
            customer=self.customer,
            order_code="TEST-01",
            total_amount=Decimal("1500000"),
            status=Order.Status.COMPLETED,
            order_date=timezone.localdate(),
        )
        self.assertEqual(self.customer.total_spent, Decimal("1500000"))

    def test_customer_string(self):
        self.assertEqual(str(self.customer), "Nguyễn An")

    def test_setup_analytics_skips_non_postgresql_database(self):
        output = StringIO()
        call_command("setup_analytics", stdout=output)
        self.assertIn("yêu cầu PostgreSQL", output.getvalue())


@override_settings(AI_PROVIDER="mock", OPENAI_API_KEY="")
class AIServiceTests(CRMBaseTest):
    def test_vip_classification(self):
        Order.objects.create(
            customer=self.customer,
            order_code="VIP-01",
            total_amount=Decimal("25000000"),
            status=Order.Status.COMPLETED,
            order_date=timezone.localdate(),
        )
        result, provider = classify_customer(self.customer)
        self.assertEqual(result["segment"], Customer.Segment.VIP)
        self.assertEqual(provider, "mock")

    def test_at_risk_classification(self):
        Order.objects.create(
            customer=self.customer,
            order_code="OLD-01",
            total_amount=Decimal("1000000"),
            status=Order.Status.COMPLETED,
            order_date=timezone.localdate() - timedelta(days=140),
        )
        result, _ = classify_customer(self.customer)
        self.assertEqual(result["segment"], Customer.Segment.AT_RISK)

    def test_email_suggestion(self):
        content, provider = suggest_email(self.customer)
        self.assertIn("Nguyễn An", content)
        self.assertEqual(provider, "mock")


@override_settings(AI_PROVIDER="mock", OPENAI_API_KEY="")
class ViewTests(CRMBaseTest):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("crm:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_for_logged_in_user(self):
        self.client.login(username="tester", password="safe-test-password")
        response = self.client.get(reverse("crm:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tổng quan kinh doanh")

    def test_analytics_requires_login(self):
        response = self.client.get(reverse("crm:analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_analytics_page_for_logged_in_user(self):
        self.client.login(username="tester", password="safe-test-password")
        response = self.client.get(reverse("crm:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phân tích dữ liệu với Superset")
        self.assertContains(response, "analytics.customer_360")

    def test_create_customer(self):
        self.client.login(username="tester", password="safe-test-password")
        response = self.client.post(
            reverse("crm:customer_create"),
            {
                "full_name": "Trần Bình",
                "email": "binh@example.com",
                "phone": "0909000000",
                "company": "Bình Minh",
                "status": Customer.Status.LEAD,
                "source": "Website",
                "notes": "Khách hàng thử nghiệm",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(email="binh@example.com").exists())

    def test_ai_classify_action_updates_customer_and_log(self):
        self.client.login(username="tester", password="safe-test-password")
        response = self.client.post(reverse("crm:ai_classify", args=[self.customer.pk]))
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertNotEqual(self.customer.ai_segment, Customer.Segment.UNCLASSIFIED)
        self.assertEqual(AIActionLog.objects.filter(customer=self.customer).count(), 1)
