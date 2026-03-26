import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsu_backend.settings')
django.setup()

from django.contrib.auth.models import User

new_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme123')
user = User.objects.get(username='admin')
user.set_password(new_password)
user.save()
print("Password reset success")