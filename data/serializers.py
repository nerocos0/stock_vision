from rest_framework import serializers

from .models import Candle, Instrument

class CandleSerializer(serializers.ModelSerializer):
    instrument = serializers.CharField(source='instrument.code', read_only=True)
    
    class Meta:
        model = Candle
        fields = ['id' ,'instrument', 'timeframe', 'datetime', 'open_price', 'high_price', 'low_price', 'close_price']
        read_only_fields = fields


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ['id', 'code', 'name', 'instrument_type', 'is_active']
        read_only_fields = fields