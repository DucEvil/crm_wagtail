from wagtail.snippets.models import register_snippet

from .models import AIActionLog, Customer, Order

register_snippet(Customer)
register_snippet(Order)
register_snippet(AIActionLog)
