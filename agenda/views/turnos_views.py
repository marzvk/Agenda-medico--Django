from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from agenda.models import Slot, Paciente, Turno, Medico
from django.contrib import messages
from agenda.services.turno_service import TurnoService
from django.core.exceptions import ValidationError
from datetime import date, timedelta


def index(request):
    return render(request, "index.html")


def lista_slots(request):

    fecha_query = request.GET.get("fecha")
    medico_id = request.GET.get("medico")

    hoy = date.today()
    manana = hoy + timedelta(days=1)

    slots = (
        Slot.objects.filter(disponible=True)
        .select_related("medico")
        .order_by("fecha", "hora_inicio")
    )

    if fecha_query:
        slots = slots.filter(fecha=fecha_query)
    elif not medico_id:
        slots = slots.filter(fecha__gte=hoy)

    if medico_id:
        slots = slots.filter(medico_id=medico_id)

    context = {
        "slots": slots,
        "medicos": Medico.objects.all(),
        "fecha_actual": fecha_query or str(hoy),
        "hoy_str": str(hoy),
        "manana_str": str(manana),
    }
    return render(request, "agenda/slots/lista_slots.html", context)


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
        request,
        "agenda/turnos/reservar_turno.html",
        {"slot": slot, "pacientes": pacientes},
    )


def lista_turnos(request):

    turnos = (
        Turno.objects.select_related("slot", "paciente")
        .exclude(estado=Turno.EstadoTurno.CANCELADO)
        .order_by("slot__fecha", "slot__hora_inicio")
    )

    return render(request, "agenda/turnos/lista_turnos.html", {"turnos": turnos})


def cancelar_turno(request, turno_id):

    turno = get_object_or_404(Turno, id=turno_id)

    TurnoService.cancelar_turno(turno)

    messages.success(request, "Turno cancelado.")

    return redirect("agenda:lista_turnos")
