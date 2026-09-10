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


def gestor_ti_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_perfil(request.user).papel != Perfil.PAPEL_GESTOR_TI:
            messages.error(request, 'Apenas o Gestor de Desenvolvimento pode acessar esta área.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def gestor_ou_ti_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_perfil(request.user).papel not in (Perfil.PAPEL_GESTOR, Perfil.PAPEL_GESTOR_TI):
            messages.error(request, 'Você não tem permissão para alterar o status.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
