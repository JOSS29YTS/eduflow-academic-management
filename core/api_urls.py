from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.courses.api_views import CourseViewSet, SessionViewSet, EnrollmentViewSet
from apps.payments.api_views import PaymentViewSet, InvoiceViewSet

# Create a central DRF router
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='api-course')
router.register(r'sessions', SessionViewSet, basename='api-session')
router.register(r'enrollments', EnrollmentViewSet, basename='api-enrollment')
router.register(r'payments', PaymentViewSet, basename='api-payment')
router.register(r'invoices', InvoiceViewSet, basename='api-invoice')

# API URL patterns
urlpatterns = [
    # JWT authentication routes
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Model viewsets routes
    path('', include(router.urls)),
]
