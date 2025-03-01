from datachat.models import (
    Product,
    Outlet,
    Warehouse,
    Address,
    Invoice,
    InvoiceItem,
)
from dataclasses import dataclass
from decimal import Decimal
from django.db.models import Sum
from django.db import connection

@dataclass
class ProductResult:
    product: Product
    total: Decimal

@dataclass
class CalculationResult:
    outlet: Outlet
    product_results: list[ProductResult]

@dataclass
class TableResult:
    col_headers: list[str]
    row_data: list[tuple]    

def prompt_1_expected_result() -> list[CalculationResult]:
    results = []
    p1 = Product.objects.get(product_code="D0001")
    p2 = Product.objects.get(product_code="R0001")
    all_outlets = Outlet.objects.all()
    for outlet in all_outlets:
        all_outlete_invoices = Invoice.objects.filter(origin_address=outlet.address).all()
        p1_total = Decimal("0.00")
        p2_total = Decimal("0.00")
        for invoice in all_outlete_invoices:
            p1_for_invoice = InvoiceItem.objects.filter(
                invoice=invoice,
                product=p1
            ).aggregate(Sum('line_total'))["line_total__sum"]
            p2_for_invoice = InvoiceItem.objects.filter(
                invoice=invoice,
                product=p2
            ).aggregate(Sum('line_total'))["line_total__sum"]
            if p1_for_invoice is not None:
                p1_total += p1_for_invoice
            if p2_for_invoice is not None:
                p2_total += p2_for_invoice
        p1_result = ProductResult(p1, p1_total)
        p2_result = ProductResult(p2, p2_total)
        results.append(CalculationResult(outlet, [p1_result, p2_result]))
    return results

def prompt_1_inject_raw_sql():
    sql = """
    SELECT 
        p.product_code,
        SUM(CASE WHEN o.name = 'Outlet 1' THEN ii.line_total ELSE 0 END) AS "Outlet 1",
        SUM(CASE WHEN o.name = 'Outlet 2' THEN ii.line_total ELSE 0 END) AS "Outlet 2",
        SUM(CASE WHEN o.name = 'Outlet 3' THEN ii.line_total ELSE 0 END) AS "Outlet 3"
    FROM datachat_outlet o
    JOIN datachat_invoice i ON i.origin_address_id = o.address_id
    JOIN datachat_invoiceitem ii ON ii.invoice_id = i.id
    JOIN datachat_product p ON p.id = ii.product_id
    WHERE p.product_code IN ('D0001', 'R0001')
    GROUP BY p.product_code;
    """    
    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()
        return results   

def display_table(data_result: list[tuple]) -> TableResult:
    pass