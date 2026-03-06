from django.shortcuts import render, redirect, get_object_or_404
from ..models import Paciente
from django import forms
from django.contrib import messages
from django.db import models


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


def lista_pacientes(request):
    query = request.GET.get("q", "")

    if request.method == "POST" and "borrar" in request.POST:
        paciente_id = request.POST.get("paciente_id")
        paciente = get_object_or_404(Paciente, id=paciente_id)
        paciente.delete()
        messages.success(request, "Paciente eliminado.")
        return redirect("agenda:lista_pacientes")

    if query:
        pacientes = Paciente.objects.filter(
            models.Q(dni__icontains=query) | models.Q(apellido__icontains=query)
        ).order_by("apellido")
    else:
        pacientes = Paciente.objects.all().order_by("apellido")

    return render(
        request,
        "agenda/paciente/pacientes.html",
        {"pacientes": pacientes, "query": query},
    )


def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
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


def crear_paciente(request):
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
