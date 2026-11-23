from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.utils import timezone

#импорты для работы с почтой
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .serializers import RegisterSerializer, FavoriteInstrumentSerializer, ChangePasswordSerializer, ChangeEmailSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from .models import FavoriteInstrument, EmailChangeRequest
from data.models import Instrument
from django.contrib.auth.models import User
from .tasks import send_verification_email_task, send_password_reset_email_task, send_email_change_task

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        username = request.data.get('username')
        user = User.objects.get(username=username)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        verify_url = f'http://127.0.0.1:8000/api/auth/verify-email/{uid}/{token}/'

        send_verification_email_task.delay(user.email, verify_url)

        return response


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
            
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)

            refresh = RefreshToken.for_user(request.user)

            return Response({
                'detail': 'Пароль успешно изменен',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect('/auth/?verified=1')
        else:
            return redirect('/auth/?error=invalid_token')


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangeEmailSerializer, responses={200: None, 400: None})
    def post(self, request):
        serializer = ChangeEmailSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        new_email = serializer.validated_data['new_email']

        change_request = EmailChangeRequest.objects.create(
            user=user,
            old_email=user.email,
            new_email=new_email,
        )

        verify_url = f"http://127.0.0.1:8000/api/auth/confirm-email-change/{user.id}/{change_request.token}/"

        send_email_change_task.delay(user.email, new_email, verify_url)

        return Response({"detail": "Письмо отправлено на новый email. Проверьте почту."})


class ConfirmEmailChangeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uid, token):
        try:
            user = User.objects.get(pk=uid)
            change_request = EmailChangeRequest.objects.get(
                user=user, token=token, status=EmailChangeRequest.Status.PENDING
            )
        except (User.DoesNotExist, EmailChangeRequest.DoesNotExist):
            return redirect('/profile/?email_error=invalid')

        if change_request.is_expired():
            change_request.status = EmailChangeRequest.Status.EXPIRED
            change_request.save()
            return redirect('/profile/?email_error=expired')

        user.email = change_request.new_email
        user.save()

        change_request.status = EmailChangeRequest.Status.CONFIRMED
        change_request.confirmed_at = timezone.now()
        change_request.save()

        return redirect('/auth/?email_changed=1')


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_password_url = f'http://127.0.0.1:8000/reset-password/?uid={uid}&token={token}'

            send_password_reset_email_task.delay(email, reset_password_url)

            return Response({"detail": "Письмо отправлено"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Пароль успешно изменен"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)