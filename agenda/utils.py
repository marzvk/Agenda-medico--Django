def user_es_medico(user):
    """Retorna True si el user, posee un perfil medico vinculado."""
    return hasattr(user, "perfil_medico")


def user_es_secretaria(user):
    """Retorna True si el user pertenece al grupo Secretaria"""
    return user.groups.filter(name="Secretaria").exists()


def user_es_admin(user):
    """True si es superusuario"""
    return user.is_superuser
