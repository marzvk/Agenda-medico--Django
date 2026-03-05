from django import forms
from django.forms import inlineformset_factory
from .models import Medico, DisponibilidadSemanal


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
