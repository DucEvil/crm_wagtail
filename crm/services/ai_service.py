import json
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone


def customer_metrics(customer):
    orders = list(customer.orders.all())
    completed = [order for order in orders if order.status == "completed"]
    return {
        "name": customer.full_name,
        "company": customer.company or "Không cung cấp",
        "status": customer.get_status_display(),
        "source": customer.source or "Không rõ",
        "order_count": len(orders),
        "completed_orders": len(completed),
        "total_spent_vnd": int(sum(order.total_amount for order in completed)),
        "last_order_date": orders[0].order_date.isoformat() if orders else None,
        "notes": customer.notes[:500] if customer.notes else "",
    }


def _mock_classification(data):
    last_order = data["last_order_date"]
    old_customer = False
    if last_order:
        old_customer = timezone.localdate() - date.fromisoformat(last_order) > timedelta(days=120)

    if data["total_spent_vnd"] >= 20_000_000 or data["completed_orders"] >= 5:
        segment = "vip"
        reason = "Giá trị mua hàng hoặc tần suất giao dịch thuộc nhóm cao."
        action = "Ưu tiên chăm sóc cá nhân và gửi ưu đãi dành riêng cho khách VIP."
    elif old_customer and data["order_count"] > 0:
        segment = "at_risk"
        reason = "Khách hàng đã lâu chưa phát sinh đơn hàng mới."
        action = "Gửi email hỏi thăm kèm ưu đãi quay lại có thời hạn."
    elif data["completed_orders"] >= 2 or data["total_spent_vnd"] >= 5_000_000:
        segment = "potential"
        reason = "Khách hàng có lịch sử giao dịch tích cực và khả năng mua thêm."
        action = "Gợi ý sản phẩm bổ sung phù hợp với lịch sử mua hàng."
    else:
        segment = "new"
        reason = "Dữ liệu giao dịch còn ít, phù hợp với nhóm khách hàng mới."
        action = "Gửi nội dung giới thiệu ngắn và hướng dẫn bước tiếp theo."
    return {"segment": segment, "reason": reason, "recommended_action": action}


def _openai_text(prompt):
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.responses.create(model=settings.OPENAI_MODEL, input=prompt)
    return response.output_text.strip()

def _gemini_text(prompt):
    from google import genai

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY trong .env")

    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini không trả về nội dung")

    return text

def _ai_text(prompt):
    if settings.AI_PROVIDER == "gemini":
        return _gemini_text(prompt)

    if settings.AI_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("Chưa cấu hình OPENAI_API_KEY")
        return _openai_text(prompt)

    raise ValueError("AI_PROVIDER không hợp lệ")

def classify_customer(customer):
    data = customer_metrics(customer)
    if settings.AI_PROVIDER == "mock":
        return _mock_classification(data), "mock"

    prompt = f"""Bạn là chuyên viên CRM. Phân loại khách hàng từ dữ liệu tổng hợp sau:
{json.dumps(data, ensure_ascii=False)}
Chỉ trả về JSON hợp lệ gồm segment (một trong new, potential, vip, at_risk), reason và recommended_action. Không thêm markdown."""
    raw = _ai_text(prompt)
    clean = raw.removeprefix("```json").removesuffix("```").strip()
    result = json.loads(clean)
    if result.get("segment") not in {"new", "potential", "vip", "at_risk"}:
        raise ValueError("AI trả về phân khúc không hợp lệ")
    return result, settings.AI_PROVIDER


def suggest_email(customer):
    data = customer_metrics(customer)
    if settings.AI_PROVIDER == "mock":
        subject_by_segment = {
            "vip": "Ưu đãi đặc biệt dành riêng cho bạn",
            "potential": "Gợi ý phù hợp dành cho bạn",
            "at_risk": "Chúng tôi rất mong được gặp lại bạn",
            "new": "Chào mừng bạn đến với doanh nghiệp",
            "unclassified": "Cảm ơn bạn đã quan tâm",
        }
        subject = subject_by_segment[customer.ai_segment]
        email = (
            f"Tiêu đề: {subject}\n\n"
            f"Xin chào {customer.full_name},\n\n"
            "Cảm ơn bạn đã tin tưởng và đồng hành cùng chúng tôi. "
            "Dựa trên nhu cầu gần đây, đội ngũ xin gửi đến bạn một số lựa chọn phù hợp "
            "và sẵn sàng tư vấn khi bạn cần.\n\n"
            "Trân trọng,\nĐội ngũ Chăm sóc khách hàng"
        )
        return email, "mock"

    prompt = f"""Bạn là chuyên viên chăm sóc khách hàng. Viết email tiếng Việt ngắn gọn, lịch sự, có tiêu đề và lời kêu gọi hành động cho khách hàng sau. Không bịa ưu đãi hoặc dữ liệu cá nhân.
Dữ liệu tổng hợp: {json.dumps(data, ensure_ascii=False)}
Phân khúc: {customer.get_ai_segment_display()}
Nhận định: {customer.ai_summary}
Chỉ trả về nội dung email hoàn chỉnh."""
    return _ai_text(prompt), settings.AI_PROVIDER
