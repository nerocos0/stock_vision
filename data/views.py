import math
from django.core.cache import cache
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime, timezone
from django.utils.dateparse import parse_datetime, parse_date
from dateutil.relativedelta import relativedelta

from .models import Candle, Instrument
from .serializers import CandleSerializer, InstrumentSerializer
from .services.twelvedata import TwelveDataService
from .services.indicators import calculate_rsi, calculate_ema, calculate_sma


INDICATORS_MAP = {
    'rsi': calculate_rsi,
    'ema': calculate_ema,
    'sma': calculate_sma
}


class DateParseMixin:
    def _parse_date_param(self, date_str):
        if not date_str:
            return None
        dt = parse_datetime(date_str)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
            
        d = parse_date(date_str)
        if d is not None:
            dt = datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc)
            return dt
        return None   


class CandleView(DateParseMixin, ListAPIView):
    serializer_class = CandleSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Candle.objects.all().order_by('datetime')
        symbol = self.request.query_params.get('symbol')
        timeframe = self.request.query_params.get('timeframe')
        from_str = self.request.query_params.get('from')
        to_str = self.request.query_params.get('to')

        if symbol:
            queryset = queryset.filter(instrument__code=symbol)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)

        if from_str and timeframe:
            from_dt = self._parse_date_param(from_str)
            if from_dt:
                queryset = queryset.filter(datetime__gte=from_dt)

        if to_str and timeframe:
            to_dt = self._parse_date_param(to_str)
            if to_dt:
                queryset = queryset.filter(datetime__lte=to_dt) 
                
        return queryset

    def list(self, request, *args, **kwargs):
        symbol = self.request.query_params.get('symbol')
        timeframe = self.request.query_params.get('timeframe')
        from_str = self.request.query_params.get('from')
        to_str = self.request.query_params.get('to')

        cache_key = f'candles:{symbol}:{timeframe}:{from_str}:{to_str}'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            print(f"ВЗЯЛИ ИЗ КЭША: {cache_key}")
            return Response(cached_data)

        serialized_data = super().list(request, *args, **kwargs)

        cache.set(cache_key, serialized_data.data, timeout=240)

        return serialized_data


class InstrumentView(ReadOnlyModelViewSet):
    serializer_class = InstrumentSerializer
    lookup_field = 'code'
    lookup_url_kwarg = 'code'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code']
    ordering = ['code']

    queryset = Instrument.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def summary(self, request):

        cache_key = 'instruments_summary'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            print(f"ВЗЯЛИ ИЗ КЭША: {cache_key}")
            return Response(cached_data)

        instruments = Instrument.objects.filter(is_active=True)
        if instruments is not None:
            data_list = []
            for instrument in instruments:
                twelve_data = TwelveDataService()

                #пока преобразование оставим так, потом можно будет реализовать список известных валют
                api_symbol = f"{instrument.code[:3]}/{instrument.code[3:]}"
                data = twelve_data.get_instrument_changes(symbol=api_symbol)
                data_list.append(data)

        cache.set(cache_key, data_list, timeout=60)

        return Response(data_list)


class IndicatorView(DateParseMixin, APIView):
    def get(self, request):
        indicator_type = self.request.query_params.get('type')
        symbol = self.request.query_params.get('symbol')
        timeframe = self.request.query_params.get('timeframe')
        from_str = self.request.query_params.get('from')
        to_str = self.request.query_params.get('to')
        period = int(self.request.query_params.get('period', 14))

        cache_key = f'indicators:{symbol}:{timeframe}:{indicator_type}:{from_str}:{to_str}'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            print(f"ВЗЯЛИ ИЗ КЭША: {cache_key}")
            return Response(cached_data)

        indicators_data = self._get_indicators_data(indicator_type, symbol, timeframe, from_str, to_str, period)

        if isinstance(indicators_data, dict) and 'error' in indicators_data:
            return Response(indicators_data, status=400)        

        cache.set(cache_key, indicators_data, timeout=240)

        return Response(indicators_data)        


    def _get_indicators_data(self, indicator_type, symbol, timeframe, from_str, to_str, period):
        calculate_func = INDICATORS_MAP.get(indicator_type)
        if not calculate_func:
            return {"error": f"Индикатор '{indicator_type}' не поддерживается"}

        to_dt = self._parse_date_param(to_str) or datetime.now(timezone.utc)
        from_dt = self._parse_date_param(from_str)
        if from_dt is None:
            #Если from не передан, берем данные за последние 30 дней
            from_dt = to_dt - relativedelta(days=30)

        main_candles = list(Candle.objects.filter(
            instrument__code=symbol,
            timeframe=timeframe,
            datetime__lte=to_dt,
            datetime__gte=from_dt
            ).order_by('datetime'))

        count_main_candles = len(main_candles)

        warmup = period * 4

        warmup_candles = list(Candle.objects.filter(
            instrument__code=symbol,
            timeframe=timeframe,
            datetime__lt=from_dt,
        ).order_by('-datetime')[:warmup])
        warmup_candles.reverse()

        all_candles = warmup_candles + main_candles

        close_prices = [float(candle.close_price) for candle in all_candles]

        values = list(calculate_func(close_prices, period))
        main_values = values[-count_main_candles:]

        result = []
        for i in range(count_main_candles):
            candle = main_candles[i]
            value = main_values[i]

            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue

            timestamp = int(candle.datetime.timestamp())

            result.append({
                'time': timestamp,
                'value': round(value, 4),
            })

        return result