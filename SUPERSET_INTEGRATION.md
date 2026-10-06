# Tích hợp SmartCRM Wagtail với Apache Superset

## 1. Kiến trúc

```text
Trình duyệt ──> Wagtail CRM :8000 ──(đọc/ghi)──┐
                                                ├──> PostgreSQL :5432
Trình duyệt ──> Superset :8088 ──(chỉ đọc)─────┘       ├── public: bảng Django
                                                       └── analytics: 3 view

Superset ──(đọc/ghi metadata)──> database PostgreSQL `superset` riêng
```

`docker-compose.analytics.yml` dùng superuser `postgres` chỉ để khởi tạo, sau đó tạo ba role tách biệt cho runtime:

| Role | Mục đích | Quyền |
|---|---|---|
| `smartcrm_app` | Wagtail/Django | Đọc và ghi database CRM |
| `smartcrm_analytics` | Datasource của Superset | `CONNECT`, `USAGE analytics`, `SELECT` các view; mặc định transaction read-only |
| `superset_meta` | Metadata nội bộ Superset | Sở hữu database `superset`, không có quyền trên CRM |

Mật khẩu chỉ nằm trong `.env.analytics` (đã được `.gitignore`), không được đưa vào source hoặc giao diện CRM.

## 2. Dataset nghiệp vụ

Lệnh `python manage.py setup_analytics` tạo idempotent ba PostgreSQL view:

| Dataset | Grain | Nội dung |
|---|---|---|
| `analytics.customer_360` | Một dòng/khách hàng | Phân khúc, số đơn, doanh thu hoàn tất, giá trị đơn trung bình, ngày mua cuối |
| `analytics.sales_daily` | Một dòng/ngày có đơn | Số đơn, khách mua, doanh thu và giá trị đơn trung bình |
| `analytics.order_detail` | Một dòng/đơn hàng | Đơn hàng kết hợp khách hàng, nguồn, công ty và phân khúc |

Định nghĩa doanh thu dùng nhất quán: chỉ cộng đơn có `status = 'completed'`.

## 3. Kết nối SQLAlchemy

Trong mạng Docker, bootstrap dùng URI:

```text
postgresql+psycopg2://smartcrm_analytics:<ANALYTICS_DB_PASSWORD>@crm-db:5432/smartcrm
```

Không dùng `localhost` trong URI của container Superset vì `localhost` khi đó là chính container Superset. Nếu cấu hình thủ công, vào **Settings → Data → Database Connections → + Database**, nhập URI trên rồi chọn **Test Connection**.

## 4. Dashboard được tạo tự động

Service one-shot `superset-bootstrap` gọi REST API của Superset theo cách idempotent để tạo:

1. Tổng doanh thu — Big Number.
2. Tổng khách hàng — Big Number.
3. Xu hướng doanh thu theo ngày — Time-series Line.
4. Phân bố phân khúc AI — Pie Chart.
5. Khách hàng theo doanh thu — Table.
6. Dashboard `SmartCRM — Tổng quan kinh doanh`, slug `smartcrm-overview`.

Chạy lại bootstrap không nhân đôi asset có cùng tên/slug; cấu hình chart và layout được cập nhật.

## 5. Kiểm tra tính chính xác

Trong Django shell:

```powershell
docker compose --env-file .env.analytics -f docker-compose.analytics.yml exec wagtail python manage.py shell -c "from crm.models import Customer,Order; from django.db.models import Sum; print(Customer.objects.count()); print(Order.objects.filter(status='completed').aggregate(Sum('total_amount')))"
```

Trong PostgreSQL, kiểm tra cùng số liệu qua view:

```powershell
docker compose --env-file .env.analytics -f docker-compose.analytics.yml exec crm-db psql -U smartcrm_app -d smartcrm -c 'SELECT count(*) AS customers, sum(revenue) AS revenue FROM analytics.customer_360;'
```

Hai kết quả số khách hàng và doanh thu phải khớp với dashboard CRM và Superset. Dữ liệu Superset là truy vấn trực tiếp, nên đơn hàng mới xuất hiện khi chart được refresh mà không cần ETL.

## 6. Vận hành và bảo mật

- File Compose phục vụ demo/phát triển một máy; không phải cấu hình production HA.
- Thay toàn bộ secret/mật khẩu ví dụ, chỉ expose PostgreSQL khi thật sự cần và bật TLS khi database đi qua mạng ngoài.
- Sao lưu cả database CRM và database metadata `superset`; metadata giữ chart, dashboard và người dùng.
- Không cấp quyền ghi cho `smartcrm_analytics`; không dùng tài khoản Wagtail làm datasource Superset.
- Khi thay schema model, chạy migration rồi chạy lại `python manage.py setup_analytics` và `superset-bootstrap`.
