from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from .serializers import RegisterSerializer, FavoriteInstrumentSerializer
from .models import FavoriteInstrument
from data.models import Instrument

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class FavoriteViewSet(ModelViewSet):
    serializer_class = FavoriteInstrumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return FavoriteInstrument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        instrument_code = request.data.get('instrument')
        
        instrument = Instrument.objects.filter(code=instrument_code).first()
        
        if not instrument:
            return Response({"error": "Инструмент не найден"}, status=status.HTTP_404_NOT_FOUND)
            
        existing = FavoriteInstrument.objects.filter(user=request.user, instrument=instrument).first()
        if existing:
            return Response({"detail": "Уже в избранном"}, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)