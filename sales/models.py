import uuid

from django.core.validators import MinValueValidator
from django.db import models


class SaleOrder(models.Model):
	class PaymentMethod(models.TextChoices):
		CASH = 'CASH', 'Cash'
		CARD = 'CARD', 'Card'
		ONLINE = 'ONLINE', 'Online'

	class PaymentStatus(models.TextChoices):
		COMPLETED = 'COMPLETED', 'Completed'
		REFUNDED = 'REFUNDED', 'Refunded'
		CANCELLED = 'CANCELLED', 'Cancelled'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	invoice_number = models.CharField(max_length=50, unique=True, editable=False)
	customer_name = models.CharField(max_length=255, default='Walk-in Customer')
	customer_phone = models.CharField(max_length=30, null=True, blank=True)
	customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, related_name='sales', null=True, blank=True)
	sold_by = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='sales')
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
	discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
	tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
	grand_total = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
	payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
	payment_status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.COMPLETED)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.invoice_number:
			self.invoice_number = f'INV-{self.created_at.year if self.created_at else "2026"}-{uuid.uuid4().hex[:8].upper()}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.invoice_number


class SaleOrderItem(models.Model):
	sale_order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE, related_name='items')
	medicine = models.ForeignKey('inventory.Medicine', on_delete=models.PROTECT, related_name='sale_items')
	batch = models.ForeignKey('inventory.Batch', on_delete=models.PROTECT, related_name='sale_items')
	quantity = models.PositiveIntegerField()
	unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])


class SaleReturn(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	return_number = models.CharField(max_length=50, unique=True, editable=False)
	sale_order = models.ForeignKey(SaleOrder, on_delete=models.PROTECT, related_name='returns')
	processed_by = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='processed_returns')
	reason = models.TextField()
	refund_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.return_number:
			self.return_number = f'RET-{self.created_at.year if self.created_at else "2026"}-{uuid.uuid4().hex[:8].upper()}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.return_number


class SaleReturnItem(models.Model):
	sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
	sale_order_item = models.ForeignKey(SaleOrderItem, on_delete=models.PROTECT, related_name='return_items')
	quantity = models.PositiveIntegerField()
	refund_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
