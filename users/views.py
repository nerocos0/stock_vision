from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer, FavoriteInstrumentSerializer, ChangePasswordSerializer, ChangeEmailSerializer
from .models import FavoriteInstrument
from data.models import Instrument

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        return Response({
            "username": user.username,
            "email": user.email,
        })


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

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        items = request.data.get('items', [])
        for item in items:
            FavoriteInstrument.objects.filter(
                id=item['id'], 
                user=request.user
            ).update(order=item['order'])
        return Response({'status': 'ok'})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: None, 400: None}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Пароль успешно изменен"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangeEmailSerializer,
        responses={200: None, 400: None}
    )
    def post(self, request):
        serializer = ChangeEmailSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Почта успешно изменена"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        