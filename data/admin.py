from django.contrib import admin

from .models import Instrument, Candle

@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'instrument_type', 'is_active']
    search_fields = ['code', 'name', 'instrument_type']
    list_filter = ['instrument_type', 'is_active']
    list_editable = ['is_active']

@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):
    list_display = ['instrument', 'timeframe', 'datetime', 'open_price', 'high_price', 'low_price', 'close_price']
    search_fields = ['instrument__code', 'timeframe']
    list_filter = ['timeframe', 'datetime', 'instrument']