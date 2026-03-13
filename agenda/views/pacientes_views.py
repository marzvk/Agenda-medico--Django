from django.shortcuts import render, redirect, get_object_or_404
from ..models import Paciente, Turno
from django import forms
from django.contrib import messages
from django.db import models
from django.utils.timezone import localtime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from agenda.forms import HistoriaClinicaForm
from agenda.utils import user_es_medico


class PacienteForm(forms.ModelForm):

    posee_obra_social = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Paciente
        fields = [
            "nombre",
            "apellido",
            "dni",
            "fecha_nacimiento",
            "telefono",
            "email",
            "historia_clinica",
            "posee_obra_social",
            "obra_social",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "historia_clinica": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "obra_social": forms.TextInput(attrs={"class": "form-control"}),
        }


@login_required
def lista_pacientes(request):
    query = request.GET.get("q", "")
    es_medico = user_es_medico(request.user)

    # 1. Seguridad en la Acción de Borrar
    if request.method == "POST" and "borrar" in request.POST:
        # Solo permitimos borrar si NO es médico (es Admin/Secretaria)
        if not es_medico:
            paciente_id = request.POST.get("paciente_id")
            paciente = get_object_or_404(Paciente, id=paciente_id)
            paciente.delete()
            messages.success(request, "Paciente eliminado.")
        else:
            messages.error(request, "No tiene permisos para eliminar pacientes.")
        return redirect("agenda:lista_pacientes")

    # 2. Definir la base de pacientes según el rol
    if es_medico:
        # Solo pacientes que tienen o tuvieron turnos con este médico específico
        pacientes_base = Paciente.objects.filter(
            turnos__slot__medico=request.user.perfil_medico
        ).distinct()
    else:
        # Administradores ven todo
        pacientes_base = Paciente.objects.all()

    # 3. Aplicar la búsqueda sobre la base ya filtrada
    if query:
        pacientes = pacientes_base.filter(
            models.Q(dni__icontains=query) | models.Q(apellido__icontains=query)
        ).order_by("apellido")
    else:
        pacientes = pacientes_base.order_by("apellido")

    context = {"pacientes": pacientes, "query": query, "es_medico": es_medico}

    return render(request, "agenda/paciente/pacientes.html", context)


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if user_es_medico(request.user):
        if not paciente.turnos.filter(slot__medico=request.user.perfil_medico).exists():
            raise PermissionDenied

    form = PacienteForm(request.POST or None, instance=paciente)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Datos del paciente actualizados.")
            return redirect("agenda:lista_pacientes")

    return render(
        request,
        "agenda/paciente/paciente_form.html",
        {"form": form, "titulo": f"Editar Paciente: {paciente.apellido}"},
    )


@login_required
def crear_paciente(request):
    if user_es_medico(request.user):
        raise PermissionDenied

    form = PacienteForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Paciente registrado con éxito.")
            return redirect("agenda:lista_pacientes")

    return render(
        request,
        "agenda/paciente/paciente_form.html",
        {"form": form, "titulo": "Nuevo Paciente"},
    )


@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    es_medico = user_es_medico(request.user)

    if es_medico:
        if not paciente.turnos.filter(slot__medico=request.user.perfil_medico).exists():
            raise PermissionDenied

    turnos_base = paciente.turnos.all()

    if es_medico:

        turnos_base = turnos_base.filter(slot__medico=request.user.perfil_medico)

    proximos_turnos = turnos_base.filter(
        slot__fecha__gte=timezone.now().date()
    ).order_by("slot__fecha")

    historial_turnos = turnos_base.filter(
        slot__fecha__lt=timezone.now().date()
    ).order_by("-slot__fecha")

    context = {
        "paciente": paciente,
        "proximos_turnos": proximos_turnos,
        "historial_turnos": historial_turnos,
        "es_medico": es_medico,
    }
    return render(request, "agenda/paciente/detalle_paciente.html", context)


#
@login_required
def editar_historia(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    # Solo médicos pueden editar historia clínica
    if not user_es_medico(request.user):
        raise PermissionDenied

    # Escudo: solo el médico que lo atendió
    if not paciente.turnos.filter(slot__medico=request.user.perfil_medico).exists():
        raise PermissionDenied

    if request.method == "POST":
        form = HistoriaClinicaForm(request.POST, instance=paciente)
        if form.is_valid():
            # Lógica de la fecha: recuperamos el texto nuevo
            nueva_nota = form.cleaned_data.get("historia_clinica")
            fecha_str = localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")

            # Guardamos con el encabezado de fecha
            paciente.historia_clinica = f"--- {fecha_str} ---\n{nueva_nota}\n\n"
            paciente.save()

            messages.success(request, "Evolución guardada.")
            return redirect("agenda:detalle_paciente", paciente_id=paciente.id)
    else:
        form = HistoriaClinicaForm(instance=paciente)

    return render(
        request,
        "agenda/paciente/editar_historia.html",
        {"form": form, "paciente": paciente},
    )
