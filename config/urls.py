from django.contrib import admin
from django.urls import path, include

from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('data.urls')),
    path('api/auth/', include('users.urls')),

    path('auth/', TemplateView.as_view(template_name='auth.html'), name='auth'),
    path('', TemplateView.as_view(template_name='index.html'), name='dashboard'),
    path('chart/', TemplateView.as_view(template_name='chart.html'), name='chart'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),    
]
