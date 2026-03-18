from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

# Register your models here.
from .models import (
    Medico,
    Paciente,
    Turno,
    Slot,
    DisponibilidadSemanal,
    TokenVerificacion,
)

admin.site.register(
    [Medico, Paciente, Turno, Slot, DisponibilidadSemanal, TokenVerificacion]
)


class UserCreationFormConEmail(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Obligatorio. El usuario recibirá el mail de activación acá.",
    )

    class Meta:
        model = User
        fields = ("username", "email")


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationFormConEmail
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
