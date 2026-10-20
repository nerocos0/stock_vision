from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import RegisterSerializer, FavoriteInstrumentSerializer
from .models import FavoriteInstrument

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
