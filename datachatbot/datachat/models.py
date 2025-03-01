from django.db import models
from datachat.config import AddressType

class Address(models.Model):
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)

class Product(models.Model):
    product_code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

class Outlet(models.Model):
    name = models.CharField(max_length=255)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name="outlet")

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name="warehouse")

class Invoice(models.Model):
    invoice_id = models.CharField(max_length=255, unique=True)
    subtotal = models.DecimalField(decimal_places=2, max_digits=10)
    gst = models.DecimalField(decimal_places=2, max_digits=10)
    total = models.DecimalField(decimal_places=2, max_digits=10)
    origin_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="invoice")
    origin_address_type = models.IntegerField(choices=[(tag.value, tag.name) for tag in AddressType])        

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(decimal_places=2, max_digits=10)
    line_total = models.DecimalField(decimal_places=2, max_digits=10)    