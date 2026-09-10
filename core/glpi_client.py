import requests
from django.conf import settings


class GlpiIntegrationError(Exception):
    pass


class GlpiClient:
    def __init__(self):
        self.base_url = settings.GLPI_API_URL
        self.app_token = settings.GLPI_APP_TOKEN
        self.user_token = settings.GLPI_USER_TOKEN
        self.timeout = 10
        self.session_token = None

    def is_configured(self):
        return bool(self.base_url and self.app_token and self.user_token)

    def init_session(self):
        headers = {
            'App-Token': self.app_token,
            'Authorization': f'user_token {self.user_token}',
        }
        try:
            response = requests.get(
                f'{self.base_url}/initSession',
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GlpiIntegrationError(f'Falha ao autenticar no GLPI: {exc}') from exc

        self.session_token = response.json().get('session_token')
        if not self.session_token:
            raise GlpiIntegrationError('GLPI não retornou session_token válido.')
        return self.session_token

    def _headers(self):
        return {
            'App-Token': self.app_token,
            'Session-Token': self.session_token,
            'Content-Type': 'application/json',
        }

    def create_ticket(self, titulo, descricao, categoria, prioridade):
        prioridade_map = {'Baixa': 2, 'Media': 3, 'Alta': 4, 'Urgente': 5}
        payload = {
            'input': {
                'name': titulo,
                'content': f'{descricao}\n\nCategoria: {categoria}',
                'priority': prioridade_map.get(prioridade, 3),
            }
        }
        try:
            response = requests.post(
                f'{self.base_url}/Ticket/',
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GlpiIntegrationError(f'Falha ao criar chamado no GLPI: {exc}') from exc

        data = response.json()
        ticket_id = data.get('id') if isinstance(data, dict) else None
        if not ticket_id:
            raise GlpiIntegrationError('GLPI não retornou o ID do chamado criado.')
        return ticket_id

    def get_ticket_status(self, ticket_id):
        try:
            response = requests.get(
                f'{self.base_url}/Ticket/{ticket_id}',
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GlpiIntegrationError(f'Falha ao consultar chamado no GLPI: {exc}') from exc
        return response.json()

    def kill_session(self):
        if not self.session_token:
            return
        try:
            requests.get(
                f'{self.base_url}/killSession',
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException:
            pass
        finally:
            self.session_token = None
