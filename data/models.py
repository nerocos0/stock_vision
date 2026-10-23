from django.db import models

class InstrumentType(models.TextChoices):
    STOCK = 'INDEX', 'Index'
    FOREX = 'FOREX', 'Forex'
    CRYPTO = 'CRYPTO', 'Crypto'


class Instrument(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    instrument_type = models.CharField(max_length=50, choices=InstrumentType.choices)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Candle(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='candles')
    timeframe = models.CharField(max_length=10)
    datetime = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=10)
    high_price = models.DecimalField(max_digits=20, decimal_places=10)
    low_price = models.DecimalField(max_digits=20, decimal_places=10)
    close_price = models.DecimalField(max_digits=20, decimal_places=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['instrument', 'timeframe', 'datetime'], name='unique_candle')
        ]
        indexes = [
            models.Index(fields=['instrument', 'timeframe', 'datetime']),
        ]
        ordering = ['-datetime']

    def __str__(self):
        return f"{self.instrument.code}  {self.timeframe} {self.datetime}"
