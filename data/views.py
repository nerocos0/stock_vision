from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime, timezone
from django.utils.dateparse import parse_datetime, parse_date

from .models import Candle, Instrument
from .serializers import CandleSerializer, InstrumentSerializer
from .services.twelvedata import TwelveDataService


class CandleView(ListAPIView):
    serializer_class = CandleSerializer

    def _parse_date_param(self, date_str):
        if not date_str:
            return None
        dt = parse_datetime(date_str)
        if dt is None:
            dt = parse_date(date_str)
            if dt is not None:
                dt = datetime.combine(dt, datetime.min.time()).replace(tzinfo=timezone.utc)
        return dt

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

