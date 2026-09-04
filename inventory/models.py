import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class MedicineReference(models.Model):
	name = models.CharField(max_length=255, db_index=True)
	company = models.CharField(max_length=255, blank=True)
	pack_size = models.CharField(max_length=255, blank=True)
	sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	mrp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	source_link = models.URLField(max_length=500, blank=True)
	letter = models.CharField(max_length=10, blank=True, db_index=True)
	imported_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['name', 'company', 'pack_size'], name='unique_reference_medicine')]
		ordering = ['name']

	def __str__(self):
		return self.name


class Medicine(models.Model):
	class UnitType(models.TextChoices):
		TABLET = 'TABLET', 'Tablet'
		STRIP = 'STRIP', 'Strip'
		SYRUP = 'SYRUP', 'Syrup'
		INJECTION = 'INJECTION', 'Injection'
		BOTTLE = 'BOTTLE', 'Bottle'
		BOX = 'BOX', 'Box'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=255)
	generic_name = models.CharField(max_length=255)
	barcode = models.CharField(max_length=100, unique=True, db_index=True)
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='medicines')
	unit_type = models.CharField(max_length=20, choices=UnitType.choices)
	shelf_location = models.CharField(max_length=100, blank=True)
	reorder_level = models.PositiveIntegerField(default=0)
	is_prescription_required = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Batch(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='batches')
	batch_number = models.CharField(max_length=100)
	manufacture_date = models.DateField()
	expiry_date = models.DateField(db_index=True)
	purchase_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	quantity = models.PositiveIntegerField(default=0)
	supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, related_name='batches', null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['medicine', 'batch_number'], name='unique_medicine_batch_number')]
		ordering = ['expiry_date']

	def __str__(self):
		return f'{self.medicine} — {self.batch_number}'
