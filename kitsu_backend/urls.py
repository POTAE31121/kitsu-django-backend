# kitsu_backend/urls.py (The Final, Correct Version)
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
# --- เพิ่ม import นี้เข้ามา ---
from rest_framework.authtoken.views import obtain_auth_token
from .views import proxy_view
from django.views.generic import RedirectView

urlpatterns = [
    # เส้นทางสำหรับแผงผู้ดูแลระบบ
    path('', RedirectView.as_view(url='https://potae31121.github.io/kitsu-cloud-kitchen/', permanent=False), name='index'),  # Redirect to the homepage

    path('admin/', admin.site.urls),
    
    # --- เพิ่มเส้นทางสำหรับ Login เข้ามาใหม่ตรงนี้ ---
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # โอนสายที่เหลือใน api/ ไปให้แผนก menu
    path('api/', include('menu.urls')),

    # เส้นทางสำหรับ proxy
    re_path(r'^proxy/(?P<path>.*)$', proxy_view),
]
# เพิ่มเส้นทางสำหรับ Media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)