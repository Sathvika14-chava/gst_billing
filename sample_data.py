"""
Sample data loader. Run with:
    python manage.py shell < sample_data.py
"""
from billing.models import Customer, Product

# Customers
Customer.objects.get_or_create(
    name="Acme Technologies Pvt Ltd",
    defaults={
        "gst_number": "36AABCA1234A1ZX",
        "state": "Telangana",
        "address": "Plot 45, HITEC City, Hyderabad - 500081",
        "phone": "+91 98765 43210",
        "email": "accounts@acme.in",
    }
)

Customer.objects.get_or_create(
    name="GlobalSoft Solutions",
    defaults={
        "gst_number": "27AABCG5678B2ZY",
        "state": "Maharashtra",
        "address": "801 BKC Tower, Bandra East, Mumbai - 400051",
        "phone": "+91 98765 11111",
        "email": "finance@globalsoft.com",
    }
)

Customer.objects.get_or_create(
    name="Sunrise Traders",
    defaults={
        "gst_number": "",
        "state": "Karnataka",
        "address": "12, MG Road, Bengaluru - 560001",
        "phone": "+91 80000 55555",
        "email": "purchase@sunrise.in",
    }
)

print("✅ Customers created")

# Products / Services
Product.objects.get_or_create(
    name="Web Development",
    defaults={
        "description": "Full-stack web application development",
        "price": 50000.00,
        "gst_rate": 18,
        "hsn_code": "998314",
        "unit": "Project",
    }
)

Product.objects.get_or_create(
    name="Annual Support Contract",
    defaults={
        "description": "12-month software support & maintenance",
        "price": 25000.00,
        "gst_rate": 18,
        "hsn_code": "998313",
        "unit": "Year",
    }
)

Product.objects.get_or_create(
    name="UI/UX Design",
    defaults={
        "description": "User interface and experience design",
        "price": 15000.00,
        "gst_rate": 18,
        "hsn_code": "998391",
        "unit": "Project",
    }
)

Product.objects.get_or_create(
    name="Cloud Hosting (Monthly)",
    defaults={
        "description": "Managed cloud server hosting",
        "price": 5000.00,
        "gst_rate": 18,
        "hsn_code": "998315",
        "unit": "Month",
    }
)

Product.objects.get_or_create(
    name="Domain Registration",
    defaults={
        "description": ".com domain for 1 year",
        "price": 800.00,
        "gst_rate": 18,
        "hsn_code": "998316",
        "unit": "Year",
    }
)

print("✅ Products created")
print("\n🎉 Sample data loaded! Now go create an invoice at http://127.0.0.1:8000/invoices/create/")
