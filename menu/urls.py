# kitsu_backend/urls.py (The Absolute Minimal & Correct Version)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. เส้นทางสำหรับหน้า Admin
    path('admin/', admin.site.urls),
    
    # 2. เส้นทางสำหรับ API ทั้งหมดของเรา
    path('api/', include('menu.urls')),
]

# หมายเหตุ: เราไม่จำเป็นต้องเพิ่ม `static(settings.MEDIA_URL, ...)` ที่นี่
# เพราะ Whitenoise จะจัดการไฟล์ static ของ Admin โดยอัตโนมัติ
# และ Cloudinary จะให้บริการไฟล์ media ผ่าน URL ของมันเองโดยตรง