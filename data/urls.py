from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandleView, InstrumentView, IndicatorView

app_name = 'data'

router = DefaultRouter()
router.register(r'candles', CandleView, basename='candles')
router.register(r'instruments', InstrumentView, basename='instruments')

urlpatterns = [
    path('indicators/', IndicatorView.as_view(), name='indicator'),
    path('', include(router.urls)),
]