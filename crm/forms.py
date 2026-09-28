from django import forms

from .models import Customer, Order


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class CustomerForm(StyledModelForm):
    class Meta:
        model = Customer
        fields = ["full_name", "email", "phone", "company", "status", "source", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}


class OrderForm(StyledModelForm):
    class Meta:
        model = Order
        fields = ["customer", "order_code", "total_amount", "status", "order_date", "notes"]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
