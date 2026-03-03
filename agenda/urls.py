from django.urls import path
from . import views

app_name = "agenda"

urlpatterns = [
    path("", views.index, name="index"),
    path("slots/", views.lista_slots, name="lista_slots"),
]
