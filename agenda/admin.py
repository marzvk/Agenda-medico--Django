from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
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
    rol = forms.ChoiceField(
        choices=[
            ("secretaria", "Secretaria"),
            ("medico", "Medico"),
        ],
        required=True,
        help_text="Define rola del usuario en el sistema.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "rol")


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationFormConEmail
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "rol"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        save_model se ejecuta cuando el admin guarda el objeto.
        Acá interceptamos el guardado para asignar el rol
        después de que el usuario fue creado.
        change=False significa que es una creación, no una edición.
        """
        super().save_model(request, obj, form, change)

        if not change:
            rol = form.cleaned_data.get("rol")
            if rol == "secretaria":
                grupo = Group.objects.get(name="Secretaria")
                obj.groups.add(grupo)

            # el perfil Medico se crea por separado en el admin


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
