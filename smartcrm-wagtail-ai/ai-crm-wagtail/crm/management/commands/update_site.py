import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cập nhật hostname của Wagtail default site từ biến WAGTAIL_SITE_HOSTNAME"

    def handle(self, *args, **options):
        # Only import after Django is fully set up
        from wagtail.models import Site

        hostname = os.getenv("WAGTAIL_SITE_HOSTNAME", "").strip()
        if not hostname:
            self.stdout.write("Bỏ qua: WAGTAIL_SITE_HOSTNAME chưa được cấu hình.")
            return

        site = Site.objects.filter(is_default_site=True).first()
        if site and site.hostname != hostname:
            site.hostname = hostname
            site.site_name = os.getenv("WAGTAIL_SITE_NAME", "SmartCRM")
            site.save()
            self.stdout.write(self.style.SUCCESS(f"Đã cập nhật hostname → {hostname}"))
        elif site:
            self.stdout.write(f"Hostname đã đúng: {hostname}")
        else:
            self.stdout.write(self.style.WARNING("Không tìm thấy default site."))
