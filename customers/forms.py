from django import forms


class EnquiryForm(forms.Form):
    customer_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    customer_phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={"class": "form-control"}))
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={"class": "form-control"}))

