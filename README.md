##El sistema utiliza una arquitectura basada en Slots.

-El médico define duración fija de consulta.

-Las disponibilidades semanales generan slots futuros automáticamente.

-Cada turno ocupa exactamente un slot.

-No existe validación de solapamiento en Turno.

-La disponibilidad se controla exclusivamente mediante el modelo Slot.

-La lógica de negocio se encuentra en services (SlotService y TurnoService).

-Se garantiza consistencia mediante transacciones atómicas y bloqueo(select_for_update).

-Se aplica restricción estructural OneToOne entre Slot y Turno.
