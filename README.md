# SmartCRM — Wagtail + AI

SmartCRM là bài tập minh họa một hệ thống kinh doanh thông minh: quản lý khách hàng, đơn hàng, phân loại khách hàng bằng AI và gợi ý email chăm sóc. Giao diện người dùng bằng tiếng Việt, responsive và có trang quản trị Wagtail.

## Tính năng

- CRUD khách hàng và đơn hàng.
- Dashboard thống kê số khách hàng, đơn hàng, doanh thu và phân khúc.
- AI phân loại: Khách hàng mới, Tiềm năng, VIP, Có nguy cơ rời bỏ.
- AI gợi ý email chăm sóc theo hồ sơ khách hàng.
- Nhật ký tác vụ AI để kiểm tra kết quả.
- Wagtail Admin tại `/admin/` và giao diện CRM tại `/crm/`.
- Chế độ `mock` chạy được ngay, không cần API key; hỗ trợ Gemini khi cấu hình khóa.

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

Bộ 9 test kiểm tra model, đăng nhập, CRUD khách hàng, phân loại AI, gợi ý email và nhật ký AI.


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
