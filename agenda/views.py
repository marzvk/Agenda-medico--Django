from django.shortcuts import render
from django.http import HttpResponse
from agenda.models import Slot


def index(request):
    return HttpResponse("Hello, world. You're at the agenda index.")


def lista_slots(request):

    slots = Slot.objects.filter(disponible=True).order_by("fecha", "hora_inicio")

    return render(request, "agenda/lista_slots.html", {"slots": slots})
