from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from agenda.models import Slot, Paciente, Turno, Medico
from django.contrib import messages
from agenda.services.turno_service import TurnoService
from django.core.exceptions import ValidationError
from datetime import date, timedelta


def index(request):
    return render(request, "index.html")


# MOSTRAR LOS SLOTS
def lista_slots(request):

    fecha_query = request.GET.get("fecha")
    medico_id = request.GET.get("medico")

    hoy = date.today()

    proximo_disponible = (
        Slot.objects.filter(disponible=True, fecha__gt=hoy)
        .order_by("fecha")
        .values_list("fecha", flat=True)
        .first()
    )

    target_manana = (
        str(proximo_disponible) if proximo_disponible else str(hoy + timedelta(days=1))
    )

    slots = (
        Slot.objects.filter(disponible=True)
        .select_related("medico")
        .order_by("fecha", "hora_inicio")
    )

    if fecha_query:
        slots = slots.filter(fecha=fecha_query)
    elif not medico_id:
        slots = slots.filter(fecha__gte=hoy)

    medico_seleccionado = None
    if medico_id:
        slots = slots.filter(medico_id=medico_id)
        medico_seleccionado = Medico.objects.filter(id=medico_id).first()

    dias_con_slots = (
        Slot.objects.filter(disponible=True, fecha__gte=hoy)
        .values_list("fecha", flat=True)
        .distinct()
        .order_by("fecha")
    )

    context = {
        "slots": slots,
        "medicos": Medico.objects.all(),
        "fecha_actual": fecha_query or str(hoy),
        "medico_seleccionado": medico_seleccionado,
        "hoy_str": str(hoy),
        "manana_inteligente": target_manana,
        "dias_con_slots": dias_con_slots,
    }
    return render(request, "agenda/slots/lista_slots.html", context)


# TURNO RESERVA
def reservar_turno(request, slot_id):

    slot = get_object_or_404(Slot, id=slot_id)
    if not slot.disponible:
        messages.error(request, "Este turno ya fue reservado por otra persona.")
        return redirect("agenda:agenda_medico", medico_id=slot.medico.id)

    pacientes = Paciente.objects.all().order_by("apellido", "nombre")

    if request.method == "POST":
        paciente_id = request.POST.get("paciente_id")
        paciente = get_object_or_404(Paciente, id=paciente_id)

        try:
            TurnoService.crear_turno(slot, paciente)

            messages.success(request, "Turno reservado con éxito")
        except Exception as e:
            messages.error(request, f"Error al reservar: {e}")

        return redirect("agenda:agenda_medico", medico_id=slot.medico.id)

    return render(
        request,
        "agenda/turnos/reservar_turno.html",
        {"slot": slot, "pacientes": pacientes},
    )


def marcar_asistido(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    turno.estado = "AS"
    turno.save()
    messages.success(
        request, f"El paciente {turno.paciente} ha sido marcado como presente"
    )
    return redirect("agenda:lista_turnos")


# LISTA TODOS LOS TURNOS
def lista_turnos(request):

    fecha_query = request.GET.get("fecha")
    medico_id = request.GET.get("medico")
    hoy = date.today()

    turnos = (
        Turno.objects.select_related("slot__medico", "paciente")
        .exclude(estado=Turno.EstadoTurno.CANCELADO)
        .order_by("slot__fecha", "slot__hora_inicio")
    )

    medico_seleccionado = None
    if medico_id:
        turnos = turnos.filter(slot__medico_id=medico_id)
        medico_seleccionado = Medico.objects.filter(id=medico_id).first()

    if fecha_query:
        turnos = turnos.filter(slot__fecha=fecha_query)
    else:

        turnos = turnos.filter(slot__fecha__gte=hoy)

    context = {
        "turnos": turnos,
        "medicos": Medico.objects.all(),
        "medico_seleccionado": medico_seleccionado,
        "medico_seleccionado_lista": (
            [medico_seleccionado.id] if medico_seleccionado else []
        ),
        "fecha_actual": fecha_query or str(hoy),
        "hoy_str": str(hoy),
    }
    return render(request, "agenda/turnos/lista_turnos.html", context)


def cancelar_turno(request, turno_id):

    turno = get_object_or_404(Turno, id=turno_id)
    medico_id = turno.slot.medico.id

    if request.method == "POST":

        TurnoService.cancelar_turno(turno)
        messages.warning(request, f"Turno de {turno.paciente} cancelado con éxito.")
        return redirect("agenda:agenda_medico", medico_id=medico_id)

    return render(request, "agenda/turnos/confirmar_cancelacion.html", {"turno": turno})
