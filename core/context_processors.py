from .permissions import get_perfil


def perfil_context(request):
    if request.user.is_authenticated:
        return {'user_perfil': get_perfil(request.user)}
    return {}
