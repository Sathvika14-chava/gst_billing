from django.db import models
from django.utils import timezone
import datetime


# Indian states list for GST state selection
INDIAN_STATES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli', 'Dadra and Nagar Haveli'),
    ('Daman and Diu', 'Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
]

GST_RATES = [
    (0, '0%'),
    (5, '5%'),
    (12, '12%'),
    (18, '18%'),
    (28, '28%'),
]


class Customer(models.Model):
    """Represents a buyer/client."""
    name = models.CharField(max_length=200)
    gst_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="GSTIN")
    state = models.CharField(max_length=100, choices=INDIAN_STATES)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.state})"

    class Meta:
        ordering = ['name']


class Product(models.Model):
    """Represents a product or service."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit (excl. GST)")
    gst_rate = models.IntegerField(choices=GST_RATES, default=18, verbose_name="GST Rate (%)")
    hsn_code = models.CharField(max_length=10, blank=True, help_text="HSN/SAC Code")
    unit = models.CharField(max_length=20, default='Nos', help_text="Unit of measurement")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (₹{self.price})"

    class Meta:
        ordering = ['name']


class Invoice(models.Model):
    """Main invoice model."""
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)

    # Tax fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CGST")
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="SGST")
    igst = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IGST")
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Tax type flag
    is_intra_state = models.BooleanField(default=True, help_text="True = CGST+SGST, False = IGST")

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def save(self, *args, **kwargs):
        # Auto-generate invoice number on first save
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)

    def _generate_invoice_number(self):
        """Generate INV-YYYY-NNNN format invoice number."""
        year = datetime.date.today().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f"INV-{year}-"
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"INV-{year}-{new_num:04d}"

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']


class InvoiceItem(models.Model):
    """Line items within an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Unit price at time of invoice")
    gst_rate = models.IntegerField(default=18, help_text="GST rate at time of invoice")
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
