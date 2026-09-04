import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Supplier(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	company_name = models.CharField(max_length=255)
	contact_person = models.CharField(max_length=255)
	email = models.EmailField()
	phone = models.CharField(max_length=30)
	address = models.TextField()
	tax_id = models.CharField(max_length=100, blank=True, null=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['company_name']

	def __str__(self):
		return self.company_name


class PurchaseOrder(models.Model):
	class Status(models.TextChoices):
		DRAFT = 'DRAFT', 'Draft'
		ORDERED = 'ORDERED', 'Ordered'
		RECEIVED = 'RECEIVED', 'Received'
		CANCELLED = 'CANCELLED', 'Cancelled'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	po_number = models.CharField(max_length=50, unique=True)
	supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
	order_date = models.DateField()
	expected_delivery_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
	total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
	created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='purchase_orders')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.po_number


class PurchaseOrderItem(models.Model):
	purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
	medicine = models.ForeignKey('inventory.Medicine', on_delete=models.PROTECT, related_name='purchase_order_items')
	quantity_ordered = models.PositiveIntegerField()
	quantity_received = models.PositiveIntegerField(default=0)
	unit_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

	class Meta:
		constraints = [models.UniqueConstraint(fields=['purchase_order', 'medicine'], name='unique_purchase_order_medicine')]
