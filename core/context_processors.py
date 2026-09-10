from .permissions import get_perfil, pode_alterar_status, pode_atender_chamados


def perfil_context(request):
    if request.user.is_authenticated:
        perfil = get_perfil(request.user)
        return {
            'user_perfil': perfil,
            'user_pode_atender': pode_atender_chamados(perfil),
            'user_pode_alterar_status': pode_alterar_status(perfil),
        }
    return {}
