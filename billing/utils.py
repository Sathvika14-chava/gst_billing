"""
GST Calculation Utilities for India.

Logic:
- If seller_state == buyer_state → CGST + SGST (intra-state)
- If seller_state != buyer_state → IGST (inter-state)
"""

from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings


def calculate_gst(price, quantity, gst_rate, is_intra_state):
    """
    Calculate GST for a single line item.

    Args:
        price (Decimal): Unit price (exclusive of GST)
        quantity (Decimal): Quantity
        gst_rate (int): GST rate as integer percentage (5, 12, 18, 28)
        is_intra_state (bool): True = CGST+SGST, False = IGST

    Returns:
        dict with keys: taxable_amount, cgst, sgst, igst, tax_amount, total_price
    """
    price = Decimal(str(price))
    quantity = Decimal(str(quantity))
    gst_rate = Decimal(str(gst_rate))

    taxable_amount = (price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_tax = (taxable_amount * gst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if is_intra_state:
        half_tax = (total_tax / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cgst = half_tax
        sgst = total_tax - half_tax  # Ensure sum is exact
        igst = Decimal('0.00')
    else:
        cgst = Decimal('0.00')
        sgst = Decimal('0.00')
        igst = total_tax

    total_price = (taxable_amount + total_tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'taxable_amount': taxable_amount,
        'cgst': cgst,
        'sgst': sgst,
        'igst': igst,
        'tax_amount': total_tax,
        'total_price': total_price,
    }


def calculate_invoice_totals(items_data, seller_state, buyer_state):
    """
    Calculate totals for an entire invoice.

    Args:
        items_data: list of dicts with keys: price, quantity, gst_rate
        seller_state (str): Seller's state
        buyer_state (str): Buyer's state

    Returns:
        dict with invoice-level totals
    """
    is_intra_state = (seller_state.strip().lower() == buyer_state.strip().lower())

    subtotal = Decimal('0.00')
    total_cgst = Decimal('0.00')
    total_sgst = Decimal('0.00')
    total_igst = Decimal('0.00')
    total_tax = Decimal('0.00')
    calculated_items = []

    for item in items_data:
        result = calculate_gst(
            price=item['price'],
            quantity=item['quantity'],
            gst_rate=item['gst_rate'],
            is_intra_state=is_intra_state
        )
        subtotal += result['taxable_amount']
        total_cgst += result['cgst']
        total_sgst += result['sgst']
        total_igst += result['igst']
        total_tax += result['tax_amount']
        calculated_items.append({**item, **result})

    total_amount = subtotal + total_tax

    return {
        'is_intra_state': is_intra_state,
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'cgst': total_cgst.quantize(Decimal('0.01')),
        'sgst': total_sgst.quantize(Decimal('0.01')),
        'igst': total_igst.quantize(Decimal('0.01')),
        'total_tax': total_tax.quantize(Decimal('0.01')),
        'total_amount': total_amount.quantize(Decimal('0.01')),
        'items': calculated_items,
    }


def amount_in_words(amount):
    """Convert a number to Indian number words (for invoice footer)."""
    amount = int(amount)
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
            'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
            'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
            'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def words_below_100(n):
        if n < 20:
            return ones[n]
        return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')

    def words_below_1000(n):
        if n < 100:
            return words_below_100(n)
        return ones[n // 100] + ' Hundred' + (' ' + words_below_100(n % 100) if n % 100 else '')

    if amount == 0:
        return 'Zero'

    parts = []
    crore = amount // 10_000_000
    amount %= 10_000_000
    lakh = amount // 100_000
    amount %= 100_000
    thousand = amount // 1000
    amount %= 1000
    remaining = amount

    if crore:
        parts.append(words_below_1000(crore) + ' Crore')
    if lakh:
        parts.append(words_below_1000(lakh) + ' Lakh')
    if thousand:
        parts.append(words_below_1000(thousand) + ' Thousand')
    if remaining:
        parts.append(words_below_1000(remaining))

    return ' '.join(parts) + ' Rupees Only'
