from django.contrib import admin
from datachat.models import (
    Product,
    Outlet,
    Warehouse,
    Invoice,
    InvoiceItem,
    Address
)

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["product_code", "name"]

@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ["name", "address"]

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["name", "address"]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_id", "subtotal", "gst", "total", "origin_address", "origin_address_type"]

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ["invoice", "product", "quantity", "unit_price", "line_total"]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["street", "postal_code"]