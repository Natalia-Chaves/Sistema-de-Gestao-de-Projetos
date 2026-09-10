from django.shortcuts import redirect
from django.urls import reverse

from .permissions import get_perfil

CAMINHOS_LIVRES = ('/logout/', '/alterar-senha/')


class ForcarTrocaSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.path.startswith('/static/')
            and request.path not in CAMINHOS_LIVRES
            and get_perfil(request.user).senha_temporaria
        ):
            return redirect(reverse('alterar_senha'))
        return self.get_response(request)
