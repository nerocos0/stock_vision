import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from django.conf import settings

class FavoriteInstrument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_instruments')
    instrument = models.ForeignKey('data.Instrument', on_delete=models.CASCADE, related_name='favorited_by')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'instrument')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.user.username} - {self.instrument.code}"


class EmailChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает подтверждения'
        CONFIRMED = 'confirmed', 'Подтверждён'
        EXPIRED = 'expired', 'Истёк'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    old_email = models.EmailField()
    new_email = models.EmailField()
    token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"{self.user.username}: {self.old_email} -> {self.new_email} ({self.status})"