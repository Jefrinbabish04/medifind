from django import forms
from django.contrib.auth.models import User
from api.models import MedicalShop, Inventory, Medicine


class ShopRegistrationForm(forms.Form):
    shop_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    owner_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    address = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    latitude = forms.FloatField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    longitude = forms.FloatField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    license_number = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username


class ShopLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ["medicine", "stock_quantity", "price", "expiry_date"]
        widgets = {
            "medicine": forms.Select(attrs={"class": "form-select"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class MedicineQuickCreateForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "brand", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
        }

