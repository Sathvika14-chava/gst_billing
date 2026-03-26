from django.contrib import admin
from .models import Customer, Product, Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['taxable_amount', 'tax_amount', 'total_price']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'gst_number', 'phone', 'email']
    search_fields = ['name', 'gst_number', 'phone']
    list_filter = ['state']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'gst_rate', 'hsn_code', 'unit']
    search_fields = ['name', 'hsn_code']
    list_filter = ['gst_rate']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'date', 'total_amount', 'status']
    list_filter = ['status', 'is_intra_state', 'date']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['invoice_number', 'subtotal', 'cgst', 'sgst', 'igst', 'total_tax', 'total_amount']
    inlines = [InvoiceItemInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'price', 'gst_rate', 'total_price']
