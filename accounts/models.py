from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		PHARMACIST = 'PHARMACIST', 'Pharmacist'
		CASHIER = 'CASHIER', 'Cashier'

	email = models.EmailField(unique=True)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
	phone = models.CharField(max_length=30, blank=True)

	def save(self, *args, **kwargs):
		if self.is_superuser or self.is_staff:
			self.role = self.Role.ADMIN
		super().save(*args, **kwargs)

	@property
	def effective_role(self):
		return self.Role.ADMIN if self.is_superuser or self.is_staff else self.role

	def __str__(self):
		return self.username


class PharmacySettings(models.Model):
	pharmacy_name = models.CharField(max_length=255, default='MediFlow Pharmacy')
	phone = models.CharField(max_length=30, blank=True)
	email = models.EmailField(blank=True)
	address = models.TextField(blank=True)
	currency = models.CharField(max_length=3, default='PKR')
	tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5)
	receipt_footer = models.CharField(max_length=255, default='Thank you for choosing MediFlow Pharmacy.')
	auto_print_receipt = models.BooleanField(default=True)
	low_stock_notifications = models.BooleanField(default=True)
	expiry_alert_days = models.PositiveIntegerField(default=30)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	@classmethod
	def load(cls):
		settings, _ = cls.objects.get_or_create(pk=1)
		return settings

	def __str__(self):
		return self.pharmacy_name
