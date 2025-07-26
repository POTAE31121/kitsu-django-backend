# kitsu_backend/wsgi.py (The Final, Correct Version)

import os
from django.core.wsgi import get_wsgi_application

# บรรทัดนี้คือหัวใจสำคัญที่สุด มันบอก Django ว่า "แผนที่หลักของนายอยู่ที่นี่นะ!"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsu_backend.settings')

application = get_wsgi_application()