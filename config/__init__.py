from .celery import app as celery_app

# esto es lo único público de este módulo cuando se exporta
#  con : from config import *
__all__ = ("celery_app",)
