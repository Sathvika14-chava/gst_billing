from django import forms
from .models import Customer, Product, Invoice, InvoiceItem, INDIAN_STATES, GST_RATES


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'gst_number', 'state', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer / Company Name'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15-digit GSTIN (optional)'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXX XXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'gst_rate', 'hsn_code', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product / Service Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'gst_rate': forms.Select(attrs={'class': 'form-select'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'HSN / SAC Code'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nos / Kg / Hr etc.'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'date', 'due_date', 'notes', 'status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InvoiceSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search invoice no. or customer...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + Invoice.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
