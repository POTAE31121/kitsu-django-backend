# kitsu_backend/views.py

import requests
from django.http import HttpResponse

# =======================================================
#               PROXY VIEW FOR FRONTEND
# =======================================================
# URL ของ Frontend บน GitHub Pages
FRONTEND_URL = 'https://potae31121.github.io/kitsu-cloud-kitchen/'

def proxy_view(request, path):
    # สร้าง URL ที่จะไปดึงข้อมูล
    url = f"{FRONTEND_URL}{path}"
    
    # ดึงข้อมูลจาก GitHub Pages
    response = requests.get(url)
    
    # ตรวจสอบ Content-Type เพื่อให้เบราว์เซอร์แสดงผลได้ถูกต้อง (สำคัญมาก!)
    content_type = response.headers.get('Content-Type')
    
    # สร้าง HttpResponse ใหม่เพื่อส่งกลับให้ผู้ใช้
    # โดยใช้เนื้อหาและ Content-Type จาก GitHub Pages
    proxy_response = HttpResponse(
        response.content,
        content_type=content_type,
        status=response.status_code,
    )
    
    return proxy_response
