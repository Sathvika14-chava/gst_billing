import csv
import json
from decimal import Decimal
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum, Count
from django.conf import settings
from django.utils import timezone

from .models import Customer, Product, Invoice, InvoiceItem
from .forms import CustomerForm, ProductForm, InvoiceForm, InvoiceSearchForm
from .utils import calculate_invoice_totals, amount_in_words


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    total_invoices = Invoice.objects.count()
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_revenue = Invoice.objects.filter(status='paid').aggregate(
        total=Sum('total_amount'))['total'] or 0

    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]

    # Monthly revenue for chart (last 6 months)
    from django.db.models.functions import TruncMonth
    monthly_data = (
        Invoice.objects
        .filter(status='paid')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )[:6]

    context = {
        'total_invoices': total_invoices,
        'total_customers': total_customers,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'recent_invoices': recent_invoices,
        'monthly_data': list(monthly_data),
    }
    return render(request, 'billing/dashboard.html', context)


# ─── Customer Views ────────────────────────────────────────────────────────────

@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'billing/customer_list.html', {'customers': customers})


@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'billing/add_customer.html', {'form': form, 'title': 'Add Customer'})


@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'billing/add_customer.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted.')
    return redirect('customer_list')


# ─── Product Views ─────────────────────────────────────────────────────────────

@login_required
def product_list(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'billing/product_list.html', {'products': products})


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'billing/add_product.html', {'form': form, 'title': 'Add Product'})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'billing/add_product.html', {'form': form, 'title': 'Edit Product'})


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
    return redirect('product_list')


# ─── Invoice Views ─────────────────────────────────────────────────────────────

@login_required
def invoice_list(request):
    form = InvoiceSearchForm(request.GET)
    invoices = Invoice.objects.select_related('customer').all()

    if form.is_valid():
        q = form.cleaned_data.get('query')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        status = form.cleaned_data.get('status')

        if q:
            invoices = invoices.filter(
                Q(invoice_number__icontains=q) | Q(customer__name__icontains=q)
            )
        if date_from:
            invoices = invoices.filter(date__gte=date_from)
        if date_to:
            invoices = invoices.filter(date__lte=date_to)
        if status:
            invoices = invoices.filter(status=status)

    invoices = invoices.order_by('-created_at')
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices,
        'search_form': form
    })


@login_required
def create_invoice(request):
    customers = Customer.objects.all()
    products = Product.objects.all()

    # Pass products as JSON for the JS dynamic rows
    products_json = json.dumps([{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'gst_rate': p.gst_rate,
        'unit': p.unit,
    } for p in products])

    customers_json = json.dumps([{
        'id': c.id,
        'name': c.name,
        'state': c.state,
    } for c in customers])

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            customer = invoice.customer
            seller_state = getattr(settings, 'COMPANY_STATE', 'Telangana')

            # Parse line items from POST
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            prices = request.POST.getlist('price[]')
            gst_rates = request.POST.getlist('gst_rate[]')

            if not product_ids:
                messages.error(request, 'Please add at least one item.')
                return render(request, 'billing/create_invoice.html', {
                    'form': form, 'customers': customers,
                    'products': products, 'products_json': products_json
                })

            items_data = []
            for i, pid in enumerate(product_ids):
                try:
                    product = Product.objects.get(pk=pid)
                    items_data.append({
                        'product': product,
                        'price': Decimal(prices[i]),
                        'quantity': Decimal(quantities[i]),
                        'gst_rate': int(gst_rates[i]),
                    })
                except (Product.DoesNotExist, IndexError, ValueError):
                    continue

            # Calculate GST totals
            raw_items = [{'price': it['price'], 'quantity': it['quantity'], 'gst_rate': it['gst_rate']} for it in items_data]
            totals = calculate_invoice_totals(raw_items, seller_state, customer.state)

            # Save invoice
            invoice.subtotal = totals['subtotal']
            invoice.cgst = totals['cgst']
            invoice.sgst = totals['sgst']
            invoice.igst = totals['igst']
            invoice.total_tax = totals['total_tax']
            invoice.total_amount = totals['total_amount']
            invoice.is_intra_state = totals['is_intra_state']
            invoice.save()

            # Save line items
            for item, calc in zip(items_data, totals['items']):
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price'],
                    gst_rate=item['gst_rate'],
                    taxable_amount=calc['taxable_amount'],
                    tax_amount=calc['tax_amount'],
                    total_price=calc['total_price'],
                )

            messages.success(request, f'Invoice {invoice.invoice_number} created!')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()

    return render(request, 'billing/create_invoice.html', {
        'form': form,
        'customers': customers,
        'products': products,
        'products_json': products_json,
        'customers_json': customers_json,
        'seller_state': getattr(settings, 'COMPANY_STATE', 'Telangana'),
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('product').all()
    amount_words = amount_in_words(invoice.total_amount)
    company = {
        'name': settings.COMPANY_NAME,
        'address': settings.COMPANY_ADDRESS,
        'state': settings.COMPANY_STATE,
        'gstin': settings.COMPANY_GSTIN,
        'phone': settings.COMPANY_PHONE,
        'email': settings.COMPANY_EMAIL,
    }
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'amount_words': amount_words,
        'company': company,
    })


@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted.')
    return redirect('invoice_list')


@login_required
def update_invoice_status(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Invoice.STATUS_CHOICES):
            invoice.status = new_status
            invoice.save()
            messages.success(request, f'Status updated to {invoice.get_status_display()}.')
    return redirect('invoice_detail', pk=pk)


# ─── PDF Generation ────────────────────────────────────────────────────────────

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('product').all()
    amount_words = amount_in_words(invoice.total_amount)
    company = {
        'name': settings.COMPANY_NAME,
        'address': settings.COMPANY_ADDRESS,
        'state': settings.COMPANY_STATE,
        'gstin': settings.COMPANY_GSTIN,
        'phone': settings.COMPANY_PHONE,
        'email': settings.COMPANY_EMAIL,
    }

    try:
        from xhtml2pdf import pisa
        from django.template.loader import get_template

        template = get_template('billing/invoice_pdf.html')
        html = template.render({
            'invoice': invoice,
            'items': items,
            'amount_words': amount_words,
            'company': company,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        return response

    except ImportError:
        # Fallback: generate PDF with reportlab
        return _generate_pdf_reportlab(invoice, items, amount_words, company)


def _generate_pdf_reportlab(invoice, items, amount_words, company):
    """Fallback PDF generation using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('title', fontSize=18, alignment=TA_CENTER,
                                  fontName='Helvetica-Bold', spaceAfter=4)
    story.append(Paragraph("TAX INVOICE", title_style))

    # Company header
    co_style = ParagraphStyle('co', fontSize=10, alignment=TA_CENTER, spaceAfter=2)
    story.append(Paragraph(f"<b>{company['name']}</b>", co_style))
    story.append(Paragraph(company['address'], co_style))
    story.append(Paragraph(f"GSTIN: {company['gstin']} | Ph: {company['phone']}", co_style))
    story.append(Spacer(1, 6*mm))

    # Invoice meta
    meta_data = [
        ['Invoice No:', invoice.invoice_number, 'Date:', str(invoice.date)],
        ['Status:', invoice.get_status_display(), 'Customer:', invoice.customer.name],
        ['Bill To:', invoice.customer.address, 'State:', invoice.customer.state],
    ]
    if invoice.customer.gst_number:
        meta_data.append(['Customer GSTIN:', invoice.customer.gst_number, '', ''])

    meta_table = Table(meta_data, colWidths=[35*mm, 65*mm, 30*mm, 50*mm])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))

    # Items table
    header = ['#', 'Item', 'HSN', 'Qty', 'Rate (₹)', 'Taxable', 'GST%', 'Tax (₹)', 'Total (₹)']
    rows = [header]
    for i, item in enumerate(items, 1):
        rows.append([
            str(i),
            item.product.name,
            item.product.hsn_code or '-',
            str(item.quantity),
            f"{item.price:,.2f}",
            f"{item.taxable_amount:,.2f}",
            f"{item.gst_rate}%",
            f"{item.tax_amount:,.2f}",
            f"{item.total_price:,.2f}",
        ])

    items_table = Table(rows, colWidths=[8*mm, 45*mm, 18*mm, 15*mm, 20*mm, 20*mm, 12*mm, 18*mm, 22*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # Totals
    totals_data = [['Subtotal', f"₹{invoice.subtotal:,.2f}"]]
    if invoice.is_intra_state:
        totals_data.append(['CGST', f"₹{invoice.cgst:,.2f}"])
        totals_data.append(['SGST', f"₹{invoice.sgst:,.2f}"])
    else:
        totals_data.append(['IGST', f"₹{invoice.igst:,.2f}"])
    totals_data.append(['TOTAL', f"₹{invoice.total_amount:,.2f}"])

    totals_table = Table(totals_data, colWidths=[130*mm, 48*mm])
    totals_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a365d')),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 4*mm))

    note_style = ParagraphStyle('note', fontSize=9, textColor=colors.HexColor('#4a5568'))
    story.append(Paragraph(f"<i>Amount in words: {amount_words}</i>", note_style))

    if invoice.notes:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(f"Notes: {invoice.notes}", note_style))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


# ─── CSV Export ────────────────────────────────────────────────────────────────

@login_required
def export_invoices_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="invoices_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Invoice No', 'Date', 'Customer', 'State', 'Subtotal',
        'CGST', 'SGST', 'IGST', 'Total Tax', 'Total Amount', 'Status'
    ])

    invoices = Invoice.objects.select_related('customer').all()
    for inv in invoices:
        writer.writerow([
            inv.invoice_number, inv.date, inv.customer.name,
            inv.customer.state, inv.subtotal,
            inv.cgst, inv.sgst, inv.igst,
            inv.total_tax, inv.total_amount, inv.status
        ])

    return response


# ─── GST Report ────────────────────────────────────────────────────────────────

@login_required
def gst_report(request):
    from django.db.models.functions import TruncMonth

    monthly = (
        Invoice.objects
        .values('date__year', 'date__month')
        .annotate(
            count=Count('id'),
            subtotal=Sum('subtotal'),
            cgst=Sum('cgst'),
            sgst=Sum('sgst'),
            igst=Sum('igst'),
            total_tax=Sum('total_tax'),
            total_amount=Sum('total_amount'),
        )
        .order_by('-date__year', '-date__month')
    )

    return render(request, 'billing/gst_report.html', {'monthly': monthly})


# ─── AJAX: Product details ─────────────────────────────────────────────────────

@login_required
def get_product_data(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'gst_rate': product.gst_rate,
        'unit': product.unit,
    })
