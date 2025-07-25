# kitsu_backend/urls.py

from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore
from django.conf import settings # type: ignore # <--- เพิ่ม
from django.conf.urls.static import static # type: ignore # <--- เพิ่ม

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('menu.urls')), # <--- เพิ่มบรรทัดนี้
]

# เพิ่มส่วนนี้เพื่อให้สามารถแสดงรูปภาพที่อัปโหลดตอนทดสอบได้
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- เพิ่มโค้ดส่วนนี้เข้าไปที่ท้ายไฟล์ ---
# นี่คือการบอกให้ Django เสิร์ฟไฟล์จาก MEDIA_ROOT เมื่ออยู่ในโหมด DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# และนี่คือการบอกให้เสิร์ฟไฟล์ใน Production ด้วย (สำหรับ Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)