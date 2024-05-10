from django.urls import path, include
from django.contrib import admin
from core.views import ProcessViewSet
from rest_framework import routers
    
route = routers.DefaultRouter()
route.register(r"processes", ProcessViewSet, basename="processes")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(route.urls)),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
