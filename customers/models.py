import uuid

from django.db import models


class Customer(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120, blank=True)
	phone = models.CharField(max_length=30, unique=True)
	email = models.EmailField(blank=True)
	address = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['first_name', 'last_name']

	@property
	def full_name(self):
		return f'{self.first_name} {self.last_name}'.strip()

	def __str__(self):
		return self.full_name
from django.db import models

# Create your models here.
