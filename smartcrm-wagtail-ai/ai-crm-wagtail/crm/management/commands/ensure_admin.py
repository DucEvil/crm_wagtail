import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Tạo tài khoản quản trị từ biến môi trường nếu chưa tồn tại"

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "").strip()
        email = os.getenv("ADMIN_EMAIL", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("Bỏ qua tạo admin: chưa cấu hình ADMIN_USERNAME/ADMIN_PASSWORD.")
            return

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Đã tạo tài khoản quản trị {username}."))
        else:
            self.stdout.write(f"Tài khoản {username} đã tồn tại; không thay đổi mật khẩu.")
