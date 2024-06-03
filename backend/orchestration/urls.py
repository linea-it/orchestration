from django.urls import path, include
from django.contrib import admin
from core.views import ProcessViewSet
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
    
route = routers.DefaultRouter()
route.register(r"processes", ProcessViewSet, basename="processes")

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('admin/', admin.site.urls),
    path('api/', include(route.urls)),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
