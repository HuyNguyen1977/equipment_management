"""
URL configuration for equipment_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import messages

def handler404(request, exception):
    """Custom 404 handler - redirect về trang chủ"""
    messages.warning(request, 'Trang bạn tìm kiếm không tồn tại. Đã chuyển về trang chủ.')
    return redirect('equipment:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('equipment.urls')),
    path('tickets/', include('tickets.urls')),
    path('renewals/', include('renewals.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Set custom 404 handler
handler404 = handler404

