from datetime import timedelta
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Medico, DisponibilidadSemanal, Paciente


class DisponibilidadForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadSemanal
        fields = ["dias_semana", "hora_inicio", "hora_fin", "activo"]
        widgets = {
            "dias_semana": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "hora_inicio": forms.TimeInput(
                attrs={"class": "form-control form-control-sm", "type": "time"}
            ),
            "hora_fin": forms.TimeInput(
                attrs={"class": "form-control form-control-sm", "type": "time"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


DisponibilidadFormSet = inlineformset_factory(
    Medico, DisponibilidadSemanal, form=DisponibilidadForm, extra=1, can_delete=True
)


class MedicoTiempoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ["tiempo_consulta"]
        labels = {
            "tiempo_consulta": "Duración de cada turno (minutos)",
        }
        widgets = {
            "tiempo_consulta": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "15",
                    "max": "60",
                    "style": "width: 120px;",
                }
            ),
        }


# agenda/forms.py


class HistoriaClinicaForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["historia_clinica"]
        widgets = {
            "historia_clinica": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 15,
                    "placeholder": "Escriba la evolución del paciente...",
                }
            ),
        }

    def clean_historia_clinica(self):
        nota = (self.cleaned_data.get("historia_clinica") or "").strip()
        if not nota:
            raise ValidationError("La evolución no puede estar vacía.")
        return nota


class SlotForm(forms.Form):
    """Formulario para crear un slot individual de forma manual."""

    fecha = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )

    def __init__(self, *args, medico=None, **kwargs):
        self.medico = medico
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        fecha = cleaned_data.get("fecha")
        h_inicio = cleaned_data.get("hora_inicio")
        h_fin = cleaned_data.get("hora_fin")

        if fecha:
            localdate = timezone.localdate()
            if fecha < localdate:
                raise ValidationError("No se puede crear un slot en una fecha pasada.")
            if fecha > localdate + timedelta(days=365):
                raise ValidationError("La fecha seleccionada es demasiado lejana.")

        if h_inicio and h_fin:
            if h_fin <= h_inicio:
                raise ValidationError(
                    "La hora de fin debe ser posterior a la hora de inicio."
                )
            if self.medico:
                if (
                    h_inicio < self.medico.inicio_jornada
                    or h_fin > self.medico.fin_jornada
                ):
                    raise ValidationError(
                        "El horario debe estar dentro de la jornada del médico."
                    )

        return cleaned_data
