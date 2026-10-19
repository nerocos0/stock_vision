from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandleView, InstrumentView

app_name = 'data'

router = DefaultRouter()
router.register(r'instruments', InstrumentView, basename='instrument')

urlpatterns = [
    path('candles/', CandleView.as_view(), name='candle-list'),
    path('', include(router.urls)),
]