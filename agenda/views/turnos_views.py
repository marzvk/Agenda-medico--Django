from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from agenda.models import Slot, Paciente, Turno, Medico
from django.contrib import messages
from agenda.services.turno_service import TurnoService
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from agenda.utils import user_es_medico
from django.core.exceptions import PermissionDenied


def index(request):
    return render(request, "index.html")


# MOSTRAR LOS SLOTS
@login_required
def lista_slots(request):
    fecha_query = request.GET.get("fecha")
    medico_id = request.GET.get("medico")
    hoy = date.today()

    # 1. Identificar si es Médico y definir el QuerySet base
    es_medico = user_es_medico(request.user)

    if es_medico:
        medico_actual = request.user.perfil_medico
        slots_base = Slot.objects.filter(medico=medico_actual, disponible=True)
        lista_medicos = [medico_actual]
    else:
        slots_base = Slot.objects.filter(disponible=True)
        lista_medicos = Medico.objects.all()

    # 2. Lógica de "Próximo disponible" y "Días con slots" (usando el base filtrado)
    proximo_disponible = (
        slots_base.filter(fecha__gt=hoy)
        .order_by("fecha")
        .values_list("fecha", flat=True)
        .first()
    )

    target_manana = (
        str(proximo_disponible) if proximo_disponible else str(hoy + timedelta(days=1))
    )

    dias_con_slots = (
        slots_base.filter(fecha__gte=hoy)
        .values_list("fecha", flat=True)
        .distinct()
        .order_by("fecha")
    )

    # 3. Aplicar filtros de búsqueda (Fecha y Médico seleccionado)
    slots = slots_base.select_related("medico").order_by("fecha", "hora_inicio")

    if fecha_query:
        slots = slots.filter(fecha=fecha_query)
    elif not medico_id:
        slots = slots.filter(fecha__gte=hoy)

    medico_seleccionado = None
    if es_medico:
        medico_seleccionado = medico_actual
    elif medico_id:
        slots = slots.filter(medico_id=medico_id)
        medico_seleccionado = Medico.objects.filter(id=medico_id).first()

    context = {
        "slots": slots,
        "medicos": lista_medicos,
        "fecha_actual": fecha_query or str(hoy),
        "medico_seleccionado": medico_seleccionado,
        "hoy_str": str(hoy),
        "manana_inteligente": target_manana,
        "dias_con_slots": dias_con_slots,
        "es_medico": es_medico,
    }
    return render(request, "agenda/slots/lista_slots.html", context)


# TURNO RESERVA
@login_required
def reservar_turno(request, slot_id):
    if user_es_medico(request.user):
        raise PermissionDenied

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


#
@login_required
def marcar_asistido(request, turno_id):
    if user_es_medico(request.user):
        raise PermissionDenied
    turno = get_object_or_404(Turno, id=turno_id)
    turno.estado = "AS"
    turno.notas = request.POST.get("notas", "")
    turno.save()
    messages.success(
        request, f"El paciente {turno.paciente} ha sido marcado como presente"
    )
    return redirect("agenda:lista_turnos")


# LISTA TODOS LOS TURNOS
@login_required
def lista_turnos(request):

    fecha_query = request.GET.get("fecha")
    medico_id = request.GET.get("medico")
    hoy = date.today()

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    proximos_dias = []
    for i in range(6):  # Hoy + Mañana + 4 días más = 6 botones
        dia = hoy + timedelta(days=i)

        if i == 0:
            label = "Hoy"
        elif i == 1:
            label = "Mañana"
        else:

            nombre_dia = dias_semana[dia.weekday()]
            label = f"{nombre_dia} {dia.day}/{dia.month}"

        proximos_dias.append({"fecha": str(dia), "label": label})

    turnos_base = (
        Turno.objects.select_related("slot__medico", "paciente")
        .exclude(estado=Turno.EstadoTurno.CANCELADO)
        .order_by("slot__fecha", "slot__hora_inicio")
    )
    es_medico = user_es_medico(request.user)

    if es_medico:
        # Si es médico, forzamos que solo vea LO SUYO
        medico_actual = request.user.perfil_medico
        turnos = turnos_base.filter(slot__medico=medico_actual)
        medico_seleccionado = medico_actual
    else:
        # Si no es médico (Admin/Secretaria)
        turnos = turnos_base
        medico_seleccionado = None
        if medico_id:
            turnos = turnos.filter(slot__medico_id=medico_id)
            medico_seleccionado = Medico.objects.filter(id=medico_id).first()

    if fecha_query:
        turnos = turnos.filter(slot__fecha=fecha_query)
    else:

        turnos = turnos.filter(slot__fecha__range=[hoy, hoy + timedelta(days=7)])

    context = {
        "turnos": turnos,
        "medicos": Medico.objects.all(),
        "medico_seleccionado": medico_seleccionado,
        "medico_seleccionado_lista": (
            [medico_seleccionado.id] if medico_seleccionado else []
        ),
        "proximos_dias": proximos_dias,
        "fecha_actual": fecha_query or str(hoy),
        "hoy_str": str(hoy),
        "es_medico": es_medico,
    }
    return render(request, "agenda/turnos/lista_turnos.html", context)


#
@login_required
def cancelar_turno(request, turno_id):

    if user_es_medico(request.user):
        raise PermissionDenied

    turno = get_object_or_404(Turno, id=turno_id)
    medico_id = turno.slot.medico.id

    if request.method == "POST":

        TurnoService.cancelar_turno(turno)
        messages.warning(request, f"Turno de {turno.paciente} cancelado con éxito.")
        return redirect("agenda:agenda_medico", medico_id=medico_id)

    return render(request, "agenda/turnos/confirmar_cancelacion.html", {"turno": turno})
