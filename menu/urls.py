# kitsu_backend/urls.py (The Final, Clean Version)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. เส้นทางสำหรับหน้า Admin
    path('admin/', admin.site.urls),
    
    # 2. เส้นทางสำหรับ API ทั้งหมดของเรา
    path('api/', include('menu.urls')),
]

# 3. เพิ่มเส้นทางสำหรับเสิร์ฟไฟล์ Media (รูปภาพ)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)