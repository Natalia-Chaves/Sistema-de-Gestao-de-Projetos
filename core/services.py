import random

from .glpi_client import GlpiClient, GlpiIntegrationError


def _mock_chamado():
    return {'id_glpi': str(random.randint(1000, 9999)), 'origem': 'mock', 'erro': None}


def enviar_chamado_glpi(titulo, descricao, categoria, prioridade):
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
