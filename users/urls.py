from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, FavoriteViewSet, ChangePasswordView, UserProfileView, ChangeEmailView, VerifyEmailView

app_name = 'users'

router = DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorites')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('profile/change-email/', ChangeEmailView.as_view(), name='change-email'),

    path('', include(router.urls)),
]