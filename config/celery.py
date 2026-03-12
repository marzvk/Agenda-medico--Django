import os
from celery import Celery

# Le dice a Celery dónde encontrar la configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("medagenda")

# Lee toda la configuración de Celery desde settings.py
# El namespace "CELERY" significa que en settings todas las
# variables de Celery empiezan con CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodescubre tasks.py en todas las apps instaladas,
# usa @shared_task de celery para saber
app.autodiscover_tasks(["agenda.notifications"])
