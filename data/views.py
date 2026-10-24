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
        instruments = Instrument.objects.filter(is_active=True)
        if instruments is not None:
            data_list = []
            for instrument in instruments:
                twelve_data = TwelveDataService()

                #пока преобразование оставим так, потом можно будет реализовать список известных валют
                api_symbol = f"{instrument.code[:3]}/{instrument.code[3:]}"
                data = twelve_data.get_instrument_changes(symbol=api_symbol)
                data_list.append(data)

        return Response(data=data_list)

class IndicatorView(DateParseMixin, APIView):
    def get(self, request):
        indicator_type = self.request.query_params.get('type')
        symbol = self.request.query_params.get('symbol')
        timeframe = self.request.query_params.get('timeframe')
        from_str = self.request.query_params.get('from')
        to_str = self.request.query_params.get('to')
        period = int(self.request.query_params.get('period', 14))

        calculate_func = INDICATORS_MAP.get(indicator_type)
        if not calculate_func:
            return Response({"error": f"Индикатор '{indicator_type}' не поддерживается"}, status=400)

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

            timestamp = int(candle.datetime.timestamp())

            result.append({
                'time': timestamp,
                'value': round(value, 4),
            })

        return Response(result)