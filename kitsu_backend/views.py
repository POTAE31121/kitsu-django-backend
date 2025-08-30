# kitsu_backend/views.py

import requests
from django.http import HttpResponse

# URL ของ Frontend บน GitHub Pages
FRONTEND_URL = 'https://potae31121.github.io/kitsu-cloud-kitchen/'

def proxy_view(request, path):
    """
    View นี้ทำหน้าที่เป็น Proxy
    1. รับ request จาก user
    2. ไปดึงข้อมูลจาก FRONTEND_URL มาแทน
    3. ส่งข้อมูลที่ได้กลับไปให้ user
    """
    # สร้าง URL ที่จะไปดึงข้อมูล (เช่น 'https://.../about' หรือ 'https://.../static/main.css')
    url = f"{FRONTEND_URL}{path}"
    
    try:
        # ดึงข้อมูลจาก GitHub Pages
        response = requests.get(url)
        response.raise_for_status() # เช็คว่า request สำเร็จหรือไม่ (ไม่มี error 404, 500)

        # ตรวจสอบ Content-Type เพื่อให้เบราว์เซอร์แสดงผลได้ถูกต้อง
        content_type = response.headers.get('Content-Type')
        
        # สร้าง HttpResponse ใหม่เพื่อส่งกลับให้ผู้ใช้
        proxy_response = HttpResponse(
            response.content,
            content_type=content_type,
            status=response.status_code,
        )
        return proxy_response

    except requests.exceptions.RequestException as e:
        # กรณีเกิด error ในการเชื่อมต่อไปยัง frontend
        print(f"Proxy request failed: {e}")
        return HttpResponse("Error: Could not retrieve content from the frontend.", status=502) # Bad Gateway