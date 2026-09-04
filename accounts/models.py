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
