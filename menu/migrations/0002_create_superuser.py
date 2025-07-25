# menu/migrations/0002_create_superuser.py

from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # ดึงข้อมูลจาก Environment Variables ที่เราตั้งค่าไว้บน Render
    DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    DJANGO_SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'some-strong-password')
    DJANGO_SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')

    # สร้าง Superuser ถ้ายังไม่มี
    if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
        User.objects.create_superuser(
            username=DJANGO_SUPERUSER_USERNAME,
            email=DJANGO_SUPERUSER_EMAIL,
            password=DJANGO_SUPERUSER_PASSWORD
        )
        print(f"Superuser '{DJANGO_SUPERUSER_USERNAME}' created.")

class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
        # เราต้องรอให้ตาราง auth สร้างเสร็จก่อน
        ('auth', '__latest__'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]