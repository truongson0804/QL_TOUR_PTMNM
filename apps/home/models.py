from django.db import models

# Create your models here.


class ContactMessage(models.Model):
	STATUS_NEW = 'NEW'
	STATUS_READ = 'READ'
	STATUS_CHOICES = [
		(STATUS_NEW, 'Mới'),
		(STATUS_READ, 'Đã đọc'),
	]

	name = models.CharField(max_length=200)
	email = models.EmailField()
	subject = models.CharField(max_length=255, blank=True, null=True)
	message = models.TextField()
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f"{self.name} <{self.email}> - {self.subject or 'No subject'}"
