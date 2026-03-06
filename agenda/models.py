from django.db import models
from datetime import date, timedelta
from django.core.exceptions import ValidationError


class Persona(models.Model):
    nombre = models.CharField(max_length=60)
    apellido = models.CharField(max_length=35)
    dni = models.CharField(max_length=15, unique=True, db_index=True)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    class Meta:
        abstract = True

    @property
    def edad(self):
        hoy = date.today()
        return (
            hoy.year
            - self.fecha_nacimiento.year
            - (
                (hoy.month, hoy.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Medico(Persona):
    especialidad = models.CharField(max_length=35)
    matricula = models.CharField(max_length=25)
    inicio_jornada = models.TimeField(verbose_name="Hora de inicio")
    fin_jornada = models.TimeField(verbose_name="Hora fin de jornada")
    tiempo_consulta = models.PositiveIntegerField(
        default=30, verbose_name="Duracion de consulta (minutos)"
    )


class Paciente(Persona):
    historia_clinica = models.TextField()
    posee_obra_social = models.BooleanField()
    obra_social = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI: {self.dni})"


class Turno(models.Model):

    class EstadoTurno(models.TextChoices):
        PROGRAMADO = "PR", "Programado"
        ASISTIDO = "AS", "Asistido"
        CANCELADO = "CA", "Cancelado"
        AUSENTE = "AU", "Ausente"

    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="turnos"
    )

    slot = models.OneToOneField("Slot", on_delete=models.CASCADE, related_name="turno")
    notas = models.TextField(blank=True)
    estado = models.CharField(
        choices=EstadoTurno.choices,
        max_length=2,
        default=EstadoTurno.PROGRAMADO,
    )

    class Meta:
        ordering = ["slot__fecha", "slot__hora_inicio"]

    def __str__(self):
        return f"Turno: {self.paciente} - {self.slot.fecha} {self.slot.hora_inicio}"


class DisponibilidadSemanal(models.Model):

    DIAS_SEMANA = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sabado"),
        (6, "Domingo"),
    ]

    medico = models.ForeignKey(
        Medico, on_delete=models.CASCADE, related_name="disponibilidades"
    )

    dias_semana = models.IntegerField(choices=DIAS_SEMANA)

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["medico", "dias_semana", "hora_inicio"]

    def __str__(self):
        return f"{self.medico} - {self.get_dias_semana_display()} {self.hora_inicio}-{self.hora_fin}"


# MODELO SLOT
class Slot(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="slots")
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("medico", "fecha", "hora_inicio")
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.medico} {self.fecha} {self.hora_inicio}-{self.hora_fin}"
