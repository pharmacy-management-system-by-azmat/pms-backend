import uuid

from django.db import models


class Prescription(models.Model):
	class Gender(models.TextChoices):
		MALE = 'MALE', 'Male'
		FEMALE = 'FEMALE', 'Female'
		OTHER = 'OTHER', 'Other'

	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		DISPENSED = 'DISPENSED', 'Dispensed'
		PARTIAL = 'PARTIAL', 'Partial'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	prescription_number = models.CharField(max_length=50, unique=True)
	patient_name = models.CharField(max_length=255)
	patient_age = models.PositiveIntegerField(null=True, blank=True)
	patient_gender = models.CharField(max_length=10, choices=Gender.choices)
	doctor_name = models.CharField(max_length=255)
	doctor_license_no = models.CharField(max_length=100, null=True, blank=True)
	prescription_image = models.ImageField(upload_to='prescriptions/', null=True, blank=True)
	notes = models.TextField(null=True, blank=True)
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
	created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='prescriptions')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.prescription_number


class PrescriptionItem(models.Model):
	prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
	medicine = models.ForeignKey('inventory.Medicine', on_delete=models.PROTECT, related_name='prescription_items')
	dosage_instructions = models.CharField(max_length=255)
	quantity_prescribed = models.PositiveIntegerField()
	quantity_dispensed = models.PositiveIntegerField(default=0)
