from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth import views as auth_views
from apps.accounts.forms import CustomAuthenticationForm

# Configure Swagger Schema View
schema_view = get_schema_view(
   openapi.Info(
      title="EduFlow API",
      default_version='v1',
      description="Documentación interactiva de la API REST de EduFlow",
      contact=openapi.Contact(email="soporte@eduflow.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # Web Authentication & Modules
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=CustomAuthenticationForm), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('courses/', include('apps.courses.urls')),
    path('', include('apps.accounts.urls')),
    
    # API endpoints
    path('api/', include('core.api_urls')),
    
    # API Documentation (Swagger & ReDoc)
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
