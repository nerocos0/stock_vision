from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime

from .models import Candle, Instrument
from .serializers import CandleSerializer, InstrumentSerializer
from data.constants import INTERVAL_DATE_FORMAT


class CandleView(ListAPIView):
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
            from_dt = datetime.strptime(from_str, INTERVAL_DATE_FORMAT[timeframe])
            queryset = queryset.filter(datetime__gte=from_dt)

        if to_str and timeframe:
            to_dt = datetime.strptime(to_str, INTERVAL_DATE_FORMAT[timeframe])
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