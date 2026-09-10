from .permissions import get_perfil


def perfil_context(request):
    """Disponibiliza o perfil (papel/área) do usuário logado em todos os templates."""
    if request.user.is_authenticated:
        return {'user_perfil': get_perfil(request.user)}
    return {}
