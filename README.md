# SmartCRM — Wagtail + AI

SmartCRM là bài tập minh họa một hệ thống kinh doanh thông minh: quản lý khách hàng, đơn hàng, phân loại khách hàng bằng AI và gợi ý email chăm sóc. Giao diện người dùng bằng tiếng Việt, responsive và có trang quản trị Wagtail.

## Tính năng

- CRUD khách hàng và đơn hàng.
- Dashboard thống kê số khách hàng, đơn hàng, doanh thu và phân khúc.
- AI phân loại: Khách hàng mới, Tiềm năng, VIP, Có nguy cơ rời bỏ.
- AI gợi ý email chăm sóc theo hồ sơ khách hàng.
- Nhật ký tác vụ AI để kiểm tra kết quả.
- Wagtail Admin tại `/admin/` và giao diện CRM tại `/crm/`.
- Apache Superset tại cổng `8088`, dùng PostgreSQL role chỉ-đọc và dashboard mẫu tự khởi tạo.
- Chế độ `mock` chạy được ngay, không cần API key; hỗ trợ Gemini khi cấu hình khóa.

## Chạy đầy đủ CRM + Apache Superset bằng Docker

Đây là cách chạy khuyến nghị cho bài tích hợp phân tích dữ liệu. Cần Docker Desktop với lệnh `docker compose`.

```powershell
Copy-Item .env.analytics.example .env.analytics
# Thay các giá trị change-me trong .env.analytics trước khi dùng ngoài máy cá nhân.
docker compose --env-file .env.analytics -f docker-compose.analytics.yml up --build
```

Sau khi các service khỏe mạnh:

- SmartCRM: `http://localhost:8000/crm/`
- Apache Superset: `http://localhost:8088/`
- Dashboard mẫu: `http://localhost:8088/superset/dashboard/smartcrm-overview/`

Stack tự động migrate Wagtail, tạo dữ liệu mẫu, tạo ba analytics view, tài khoản chỉ-đọc, ba dataset và năm chart. Tài khoản đăng nhập lấy từ `CRM_ADMIN_*` và `SUPERSET_ADMIN_*` trong `.env.analytics`.

Cấu hình AI (`AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL` hoặc các biến OpenAI) được CRM đọc trực tiếp từ `.env`. Sau khi sửa `.env`, áp dụng lại bằng `docker compose --env-file .env.analytics -f docker-compose.analytics.yml up -d --no-deps wagtail`. Không cần dựng lại image để thay cấu hình AI.

```powershell
# Xem trạng thái
docker compose --env-file .env.analytics -f docker-compose.analytics.yml ps

# Chạy lại bước tạo dashboard nếu cần
docker compose --env-file .env.analytics -f docker-compose.analytics.yml run --rm superset-bootstrap

# Dừng stack nhưng giữ dữ liệu
docker compose --env-file .env.analytics -f docker-compose.analytics.yml down
```

Không dùng `down -v` nếu muốn giữ database. Xem [SUPERSET_INTEGRATION.md](SUPERSET_INTEGRATION.md) để biết mô hình dữ liệu, SQLAlchemy URI, cách kiểm tra số liệu và lưu ý production.

## 1. Chạy trên máy

Yêu cầu Python 3.12 trở lên.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Mở `http://127.0.0.1:8000/`, đăng nhập tại `http://127.0.0.1:8000/accounts/login/`.

## 2. Cấu hình AI

Mặc định dự án dùng thuật toán mô phỏng có thể giải thích và không cần gửi dữ liệu ra ngoài:

```env
AI_PROVIDER=mock
```

Để dùng OpenAI thật, đặt các biến môi trường (không commit khóa vào GitHub):

```env

```

Dịch vụ chỉ gửi dữ liệu tổng hợp cần thiết như số đơn, tổng chi tiêu, lần mua gần nhất; không gửi email và số điện thoại trong prompt.

## 3. Luồng trình bày cá nhân

1. Đăng nhập và giới thiệu Dashboard.
2. Vào **Khách hàng → Thêm khách hàng**.
3. Mở hồ sơ và chọn **Tạo đơn hàng**.
4. Chọn **Phân loại bằng AI**, giải thích phân khúc và hành động đề xuất.
5. Chọn **Tạo email gợi ý**, kiểm tra nội dung và nhấn **Sao chép**.
6. Mở `/admin/` để chứng minh dữ liệu cũng quản lý được qua Wagtail.

## 4. Kiểm thử

```bash
python manage.py check
python manage.py test crm
```

Bộ 12 test kiểm tra model, đăng nhập, CRUD khách hàng, phân loại AI, gợi ý email, nhật ký AI, lệnh analytics và trang tích hợp Superset.


## Cấu trúc chính

```text
crm/
├── models.py                  # Customer, Order, AIActionLog
├── forms.py                   # Form CRUD
├── views.py                   # Dashboard, CRUD, tác vụ AI
├── services/ai_service.py     # Mock AI và Gemini
├── templates/crm/             # Giao diện responsive
├── static/crm/                # CSS và JavaScript
└── tests/test_crm.py          # Kiểm thử tự động
```

Xem `BAO_CAO_BAI_TAP.md` để đối chiếu đầy đủ yêu cầu và kịch bản demo.
