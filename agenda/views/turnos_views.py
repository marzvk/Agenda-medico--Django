from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from agenda.models import Slot, Paciente, Turno
from django.contrib import messages
from agenda.services.turno_service import TurnoService
from django.core.exceptions import ValidationError


def index(request):
    return HttpResponse("Hello, world. You're at the agenda index.")


def lista_slots(request):

    slots = Slot.objects.filter(disponible=True).order_by("fecha", "hora_inicio")

    return render(request, "agenda/lista_slots.html", {"slots": slots})


def reservar_turno(request, slot_id):

    slot = get_object_or_404(Slot, id=slot_id)

    if request.method == "POST":

        paciente_id = request.POST.get("paciente_id")
        paciente = get_object_or_404(Paciente, id=paciente_id)

        try:
            TurnoService.crear_turno(slot, paciente)
            messages.success(request, "Turno reservado con exito")
            return redirect("agenda:lista_slots")

        except ValidationError as e:
            messages.error(request, str(e))

    pacientes = Paciente.objects.all()

    return render(
        request, "agenda/reservar_turno.html", {"slot": slot, "pacientes": pacientes}
    )


def lista_turnos(request):

    turnos = Turno.objects.select_related("slot", "paciente").order_by(
        "slot__fecha", "slot__hora_inicio"
    )

    return render(request, "agenda/lista_turnos.html", {"turnos": turnos})


def cancelar_turno(request, turno_id):

    turno = get_object_or_404(Turno, id=turno_id)

    TurnoService.cancelar_turno(turno)

    messages.success(request, "Turno cancelado.")

    return redirect("agenda:lista_turnos")
