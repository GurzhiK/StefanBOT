# stef/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import path, include
from django.contrib import admin

def redirect_to_docs(request):
    return redirect('admin/')

urlpatterns = [
    path('', redirect_to_docs),
    path('admin/', admin.site.urls),
    path('api/', include('stefbot.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
