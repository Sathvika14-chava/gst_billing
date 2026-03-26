# BillFlow — GST Billing System

A complete, production-ready GST-compliant invoicing web application built with Django.

## Features
- GST Calculation: Automatic CGST+SGST (intra-state) or IGST (inter-state)
- Tax Slabs: 0%, 5%, 12%, 18%, 28%
- Invoice Generation: Auto-numbered, downloadable PDF
- Dynamic Line Items: Add/remove rows with live total preview
- Invoice Management: Draft → Sent → Paid → Cancelled workflow
- Customer & Products: Full CRUD
- Search & Filter: By invoice number, customer, date range, status
- GST Report: Monthly tax summary breakup
- CSV Export: One-click export of all invoices
- Authentication: Login/logout with session management
- Admin Panel: Full Django admin interface

## Quick Setup

### Step 1 — Create & activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Configure your company details
Open `gst_billing/settings.py` and update:
```python
COMPANY_NAME    = "Your Company Name"
COMPANY_ADDRESS = "123, Business Street, City - 500001"
COMPANY_STATE   = "Telangana"   # IMPORTANT: your seller state for GST
COMPANY_GSTIN   = "36AABCU9603R1ZX"
COMPANY_PHONE   = "+91 99999 99999"
COMPANY_EMAIL   = "billing@yourcompany.com"
```

### Step 4 — Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5 — Create admin superuser
```bash
python manage.py createsuperuser
```

### Step 6 — (Optional) Load sample data
```bash
python manage.py shell
```
```python
from billing.models import Customer, Product
Customer.objects.create(name="Acme Corp Hyderabad", gst_number="36AABCU9603R1ZX",
    state="Telangana", address="Hitech City, Hyderabad", phone="9000000001")
Customer.objects.create(name="TechFirm Mumbai", gst_number="27AABCU9603R1ZX",
    state="Maharashtra", address="BKC, Mumbai", phone="9000000002")
Product.objects.create(name="Web Development", price=50000, gst_rate=18,
    hsn_code="998314", unit="Project")
Product.objects.create(name="Annual SaaS License", price=12000, gst_rate=18,
    hsn_code="997331", unit="Year")
Product.objects.create(name="Hardware - Laptop", price=80000, gst_rate=12,
    hsn_code="84713010", unit="Nos")
exit()
```

### Step 7 — Start the server
```bash
python manage.py runserver
```
Open: http://127.0.0.1:8000

## GST Logic
```
IF seller_state == buyer_state:  → CGST + SGST (each = rate/2)
ELSE:                            → IGST (= full rate)
```

## URL Reference
| URL | Page |
|-----|------|
| / | Dashboard |
| /invoices/ | Invoice list |
| /invoices/create/ | Create invoice |
| /invoices/<id>/ | Invoice detail |
| /invoices/<id>/pdf/ | Download PDF |
| /customers/ | Customers |
| /products/ | Products |
| /report/gst/ | GST Report |
| /export/csv/ | CSV Export |
| /admin/ | Django Admin |

## Tech Stack
- Backend: Django 4.2+
- Database: SQLite (swap to PostgreSQL for production)
- PDF: xhtml2pdf + reportlab (fallback)
- Frontend: Bootstrap 5.3, Bootstrap Icons, Google Fonts
