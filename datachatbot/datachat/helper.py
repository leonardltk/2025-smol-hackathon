from datachat.models import (
    Product,
    Outlet,
    Invoice,
    InvoiceItem,
    Warehouse
)
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from django.db import connection
from matplotlib import pyplot
import mpld3

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

@dataclass
class BarChartResult:
    name: str
    amount: Decimal

def prompt_1_expected_result() -> list[CalculationResult]:
    results = []
    p1 = Product.objects.get(product_code="D0001")
    p2 = Product.objects.get(product_code="R0001")
    all_outlets = Outlet.objects.all()
    for outlet in all_outlets:
        all_outlet_invoices = Invoice.objects.filter(origin_address=outlet.address).all()
        p1_total = Decimal("0.00")
        p2_total = Decimal("0.00")
        for invoice in all_outlet_invoices:
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

def prompt_2_django_orm() -> Decimal:
    total_sales = Invoice.objects.all().aggregate(Sum('total'))["total__sum"]
    warehouse_sales = Invoice.objects.filter(origin_address_type="2").aggregate(Sum('total'))["total__sum"]
    result = Decimal(warehouse_sales / total_sales)
    percentage = (result * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return percentage

def prompt_2_inject_raw_sql():
    warehouse_sale_sql = """
        SELECT SUM(total)
        FROM datachat_invoice
        WHERE origin_address_type = 2;
    """
    total_sale_sql = """
        SELECT SUM(total)
        FROM datachat_invoice
    """
    with connection.cursor() as cursor:
        cursor.execute(warehouse_sale_sql)
        res_1 = cursor.fetchall()
        warehouse_sales = res_1[0][0]
        cursor.execute(total_sale_sql)
        res_2 = cursor.fetchall()
        total_sales = res_2[0][0]
        return (Decimal(warehouse_sales / total_sales) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def prompt_3_django_orm():
    all_outlets = Outlet.objects.all()
    all_warehouses = Warehouse.objects.all()
    results = []
    for outlet in all_outlets:
        outlet_sum = Invoice.objects.filter(origin_address=outlet.address).aggregate(Sum('total'))["total__sum"]
        results.append(BarChartResult(outlet.name, outlet_sum))
    for warehouse in all_warehouses:
        warehouse_sum = Invoice.objects.filter(origin_address=warehouse.address).aggregate(Sum('total'))["total__sum"]
        results.append(BarChartResult(warehouse.name, warehouse_sum))
    x_axis = [result.name for result in results]
    y_axis = [result.amount for result in results]
    pyplot.figure()
    pyplot.bar(x_axis, y_axis)
    pyplot.title("Sales By Outlet")
    pyplot.xlabel("Locations")
    pyplot.ylabel("Sales")
    chart_html = mpld3.fig_to_html(pyplot.gcf())
    pyplot.clf()
    return chart_html

def prompt_3_sql():
    pass