from django.db import models

from django.conf import settings

class FavoriteInstrument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_instruments')
    instrument = models.ForeignKey('data.Instrument', on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'instrument')

    def __str__(self):
        return f"{self.user.username} - {self.instrument.code}"