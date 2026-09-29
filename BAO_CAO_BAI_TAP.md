# Báo cáo bài tập cá nhân — SmartCRM Wagtail + AI

## 1. Mục tiêu

Xây dựng một ứng dụng CRM nhỏ bằng Wagtail giúp doanh nghiệp lưu khách hàng, quản lý đơn hàng và ứng dụng AI vào chăm sóc khách hàng.

## 2. Đối chiếu yêu cầu

| Yêu cầu | Phần đã triển khai | Cách kiểm tra |
|---|---|---|
| Thiết lập Python và Wagtail | Django 6.1.1, Wagtail 8.0, cấu trúc project chuẩn | `python manage.py check` |
| Custom model | `Customer`, `Order`, `AIActionLog` và migration | Wagtail Admin → Snippets |
| Tích hợp AI API | Gemini API; có mock fallback | Nút “Phân loại bằng AI” và “Tạo email gợi ý” |
| Frontend tương tác | Dashboard, tìm kiếm/lọc, CRUD, responsive | Truy cập `/crm/` trên desktop/mobile |
| Kiểm thử và triển khai | 8 test tự động, `render.yaml`, `build.sh` | `python manage.py test crm`; deploy Blueprint trên Render |

## 3. Mô hình dữ liệu

- Một khách hàng có nhiều đơn hàng.
- Một khách hàng có nhiều nhật ký tác vụ AI.
- Xóa khách hàng sẽ xóa các đơn hàng và nhật ký liên quan.
- Email khách hàng và mã đơn hàng là duy nhất.

## 4. Logic AI

Đầu vào được giới hạn ở dữ liệu tổng hợp: trạng thái, nguồn, số đơn, số đơn hoàn thành, tổng chi tiêu, ngày mua gần nhất và ghi chú ngắn.

Đầu ra phân loại gồm:

- `new`: dữ liệu giao dịch còn ít.
- `potential`: đã có giao dịch tích cực.
- `vip`: doanh thu từ 20 triệu đồng hoặc ít nhất 5 đơn hoàn tất.
- `at_risk`: từng mua nhưng quá 120 ngày chưa có đơn mới.

Với Gemini, ứng dụng yêu cầu JSON có cấu trúc và kiểm tra lại giá trị phân khúc. Nếu chưa có API key, mock AI vẫn thực hiện cùng luồng giao diện để phục vụ demo.

## 5. An toàn và giới hạn

- Không lưu API key trong mã nguồn.
- Không gửi email hoặc số điện thoại khách hàng cho mô hình AI.
- Email AI chỉ là bản nháp, hệ thống không tự động gửi.
- Mọi tác vụ AI được ghi log, kể cả trường hợp lỗi.

## 6. Kịch bản kiểm thử thủ công

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| TC01 | Truy cập `/crm/` khi chưa đăng nhập | Chuyển đến trang đăng nhập |
| TC02 | Tạo khách hàng hợp lệ | Hồ sơ mới xuất hiện trong danh sách |
| TC03 | Tạo đơn hàng cho khách | Đơn xuất hiện và dashboard cập nhật |
| TC04 | Bấm phân loại AI | Phân khúc và nhận định được lưu |
| TC05 | Bấm tạo email | Bản nháp email xuất hiện và sao chép được |
| TC06 | Dùng màn hình nhỏ | Sidebar thu gọn, bảng có thể cuộn ngang |

## 7. Kết luận

Dự án đáp ứng đủ năm nhóm yêu cầu của bài tập và có thể trình bày độc lập. Điểm mở rộng trong tương lai là biểu đồ theo thời gian, phân quyền nhân viên, nhập dữ liệu CSV và gửi email sau bước phê duyệt.
