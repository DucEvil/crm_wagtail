import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Command(BaseCommand):
    help = "Tạo các PostgreSQL view chỉ-đọc dùng làm dataset cho Apache Superset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-grants",
            action="store_true",
            help="Tạo view nhưng không cấp quyền cho ANALYTICS_DB_ROLE.",
        )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "Bỏ qua analytics views: Apache Superset stack yêu cầu PostgreSQL "
                    "(cơ sở dữ liệu hiện tại không phải PostgreSQL)."
                )
            )
            return

        role = settings.ANALYTICS_DB_ROLE
        if not IDENTIFIER.fullmatch(role):
            raise CommandError("ANALYTICS_DB_ROLE phải là tên định danh PostgreSQL hợp lệ.")

        statements = [
            "CREATE SCHEMA IF NOT EXISTS analytics",
            CUSTOMER_360_VIEW,
            SALES_DAILY_VIEW,
            ORDER_DETAIL_VIEW,
        ]
        try:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

                if not options["skip_grants"]:
                    quoted_role = connection.ops.quote_name(role)
                    cursor.execute("SELECT current_database()")
                    database_name = cursor.fetchone()[0]
                    quoted_database = connection.ops.quote_name(database_name)
                    cursor.execute(
                        f"GRANT CONNECT ON DATABASE {quoted_database} TO {quoted_role}"
                    )
                    cursor.execute(f"GRANT USAGE ON SCHEMA analytics TO {quoted_role}")
                    cursor.execute(
                        f"GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO {quoted_role}"
                    )
        except Exception as exc:
            raise CommandError(
                "Không thể tạo analytics views hoặc cấp quyền. Hãy chắc chắn role "
                f"'{role}' đã tồn tại và user ứng dụng sở hữu database. Chi tiết: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Đã tạo analytics.customer_360, analytics.sales_daily và "
                "analytics.order_detail."
            )
        )


CUSTOMER_360_VIEW = """
CREATE OR REPLACE VIEW analytics.customer_360 AS
SELECT
    c.id AS customer_id,
    c.full_name,
    c.company,
    c.source,
    c.status,
    CASE c.status
        WHEN 'lead' THEN 'Tiềm năng'
        WHEN 'active' THEN 'Đang hoạt động'
        WHEN 'inactive' THEN 'Ngừng hoạt động'
        ELSE c.status
    END AS status_label,
    c.ai_segment,
    CASE c.ai_segment
        WHEN 'new' THEN 'Khách hàng mới'
        WHEN 'potential' THEN 'Khách hàng tiềm năng'
        WHEN 'vip' THEN 'Khách hàng VIP'
        WHEN 'at_risk' THEN 'Có nguy cơ rời bỏ'
        ELSE 'Chưa phân loại'
    END AS segment_label,
    c.created_at,
    c.updated_at,
    COUNT(o.id) AS order_count,
    COUNT(o.id) FILTER (WHERE o.status = 'completed') AS completed_order_count,
    COALESCE(
        SUM(o.total_amount) FILTER (WHERE o.status = 'completed'), 0
    ) AS revenue,
    COALESCE(
        AVG(o.total_amount) FILTER (WHERE o.status = 'completed'), 0
    ) AS average_order_value,
    MAX(o.order_date) AS last_order_date,
    CURRENT_DATE - MAX(o.order_date) AS days_since_last_order
FROM crm_customer c
LEFT JOIN crm_order o ON o.customer_id = c.id
GROUP BY c.id
"""


SALES_DAILY_VIEW = """
CREATE OR REPLACE VIEW analytics.sales_daily AS
SELECT
    o.order_date,
    COUNT(*) AS order_count,
    COUNT(*) FILTER (WHERE o.status = 'completed') AS completed_order_count,
    COUNT(DISTINCT o.customer_id) AS customer_count,
    COALESCE(
        SUM(o.total_amount) FILTER (WHERE o.status = 'completed'), 0
    ) AS revenue,
    COALESCE(
        AVG(o.total_amount) FILTER (WHERE o.status = 'completed'), 0
    ) AS average_order_value
FROM crm_order o
GROUP BY o.order_date
"""


ORDER_DETAIL_VIEW = """
CREATE OR REPLACE VIEW analytics.order_detail AS
SELECT
    o.id AS order_id,
    o.order_code,
    o.order_date,
    o.created_at,
    o.total_amount,
    o.status,
    CASE o.status
        WHEN 'pending' THEN 'Chờ xử lý'
        WHEN 'processing' THEN 'Đang xử lý'
        WHEN 'completed' THEN 'Hoàn thành'
        WHEN 'cancelled' THEN 'Đã hủy'
        ELSE o.status
    END AS status_label,
    c.id AS customer_id,
    c.full_name AS customer_name,
    c.company,
    c.source,
    c.ai_segment,
    CASE c.ai_segment
        WHEN 'new' THEN 'Khách hàng mới'
        WHEN 'potential' THEN 'Khách hàng tiềm năng'
        WHEN 'vip' THEN 'Khách hàng VIP'
        WHEN 'at_risk' THEN 'Có nguy cơ rời bỏ'
        ELSE 'Chưa phân loại'
    END AS segment_label
FROM crm_order o
JOIN crm_customer c ON c.id = o.customer_id
"""
