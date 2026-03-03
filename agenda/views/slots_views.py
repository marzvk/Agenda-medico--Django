from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from agenda.models import Medico
from agenda.services.slot_service import generar_slots_para_medico


# @login_required
def generar_agenda(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)

    generar_slots_para_medico(medico)

    messages.success(request, "Agenda generada correctamente.")
    return redirect("agenda:agenda_medico", medico_id=medico.id)
