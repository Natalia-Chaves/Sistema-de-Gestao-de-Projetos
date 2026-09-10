from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import Perfil


def get_perfil(user):
    perfil = getattr(user, 'perfil', None)
    if perfil is not None:
        return perfil
    papel = Perfil.PAPEL_GESTOR_TI if (user.is_superuser or user.is_staff) else Perfil.PAPEL_COLABORADOR
    return Perfil(user=user, papel=papel, area='')


def gestor_ou_ti_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_perfil(request.user).papel not in (Perfil.PAPEL_GESTOR, Perfil.PAPEL_GESTOR_TI):
            messages.error(request, 'Você não tem permissão para gerenciar usuários.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def pode_atender_chamados(perfil):
    return perfil.papel == Perfil.PAPEL_GESTOR_TI or (
        perfil.papel == Perfil.PAPEL_COLABORADOR and perfil.area == 'TI'
    )


def eh_colaborador_ti(perfil):
    return perfil.papel == Perfil.PAPEL_COLABORADOR and perfil.area == 'TI'


def pode_alterar_status(perfil):
    return perfil.papel in (Perfil.PAPEL_GESTOR, Perfil.PAPEL_GESTOR_TI) or pode_atender_chamados(perfil)


def atendente_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not pode_atender_chamados(get_perfil(request.user)):
            messages.error(request, 'Você não tem permissão para atender chamados ou projetos.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def status_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not pode_alterar_status(get_perfil(request.user)):
            messages.error(request, 'Você não tem permissão para alterar status.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
