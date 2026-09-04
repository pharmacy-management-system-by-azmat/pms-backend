from django.db import models


class StockAuditLog(models.Model):
	class ActionType(models.TextChoices):
		STOCK_ADD = 'STOCK_ADD', 'Stock added'
		DAMAGE_EXPIRE_REMOVAL = 'DAMAGE_EXPIRE_REMOVAL', 'Damage or expiry removal'
		PRICE_UPDATE = 'PRICE_UPDATE', 'Price update'
		MANUAL_CORRECTION = 'MANUAL_CORRECTION', 'Manual correction'

	user = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='stock_audits')
	batch = models.ForeignKey('inventory.Batch', on_delete=models.PROTECT, related_name='audit_logs')
	action_type = models.CharField(max_length=30, choices=ActionType.choices)
	quantity_changed = models.IntegerField()
	reason = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-timestamp']
