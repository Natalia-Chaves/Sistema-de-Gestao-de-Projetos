"""Camada de integração com o GLPI.

Tenta usar a API real do GLPI quando configurada (GLPI_API_URL, GLPI_APP_TOKEN,
GLPI_USER_TOKEN no .env). Caso não esteja configurada ou a chamada falhe,
utiliza um serviço mock (modo simulado), documentando isso no retorno em
`origem` ('real' ou 'mock') para a interface exibir isso ao usuário.
"""
import random

from .glpi_client import GlpiClient, GlpiIntegrationError


def _mock_chamado():
    return {'id_glpi': f'MOCK-{random.randint(1000, 9999)}', 'origem': 'mock', 'erro': None}


def enviar_chamado_glpi(titulo, descricao, categoria, prioridade):
    """Envia um chamado ao GLPI. Retorna dict com id_glpi, origem e erro (se houver)."""
    client = GlpiClient()

    if not client.is_configured():
        return _mock_chamado()

    try:
        client.init_session()
        ticket_id = client.create_ticket(titulo, descricao, categoria, prioridade)
        return {'id_glpi': ticket_id, 'origem': 'real', 'erro': None}
    except GlpiIntegrationError as exc:
        resultado = _mock_chamado()
        resultado['erro'] = str(exc)
        return resultado
    finally:
        client.kill_session()
