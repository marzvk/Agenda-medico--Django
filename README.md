# MedAgenda

Sistema de gestión de turnos médicos con notificaciones automáticas por email.

---

## Arquitectura general

- Proyecto Django con una sola app `agenda` y módulo `notifications`.
- La lógica de negocio vive en `services/`, separada de modelos y vistas.
- Las notificaciones viven en `notifications/`, separadas del resto de la lógica.
- Configuración centralizada en `config/`.

---

## Modelo de turnos

- El médico define duración fija de consulta.
- Las disponibilidades semanales generan slots futuros automáticamente.
- Cada turno ocupa exactamente un slot.
- La disponibilidad se controla exclusivamente mediante el modelo Slot.
- Se aplica restricción estructural OneToOne entre Slot y Turno.
- La lógica de negocio se encuentra en `services/` (SlotService y TurnoService).
- Se garantiza consistencia mediante transacciones atómicas y bloqueo `select_for_update`.

---

## Sistema de notificaciones

- Al confirmar un turno el paciente recibe un mail de confirmación inmediato.
- El paciente recibe un recordatorio configurable X horas antes del turno.
- El médico recibe un resumen diario de su agenda a la hora que configure.
- Cada médico controla individualmente sus notificaciones desde su perfil.
- Las notificaciones se ejecutan de forma asíncrona mediante Celery y Redis.
- Celery Beat programa el resumen diario según la configuración de cada médico.
- El schedule de Beat se persiste en base de datos mediante `django-celery-beat`.
- Al crear o modificar un médico una signal actualiza automáticamente su tarea en Beat.
- El sistema requiere tres procesos simultáneos: `runserver`, `celery worker` y `celery beat`.

---

## Seguridad

- RBAC: control de acceso basado en roles (Médicos y Secretarias).
- Los médicos solo acceden a sus propios pacientes y turnos.
- Protección a nivel de objeto con `PermissionDenied` en vistas de detalle y edición.
- Vista `editar_historia` exclusiva para médicos con inserción automática de fecha y hora.

---

## Stack

- Python / Django
- SQLite
- Celery + Redis
- django-celery-beat