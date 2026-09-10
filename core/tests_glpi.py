from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from .glpi_client import GlpiClient, GlpiIntegrationError
from .services import enviar_chamado_glpi

GLPI_SETTINGS = dict(
    GLPI_API_URL='https://glpi.exemplo.com/apirest.php',
    GLPI_APP_TOKEN='app-token-teste',
    GLPI_USER_TOKEN='user-token-teste',
)


class GlpiClientTests(TestCase):
    def test_is_configured_false_sem_credenciais(self):
        client = GlpiClient()
        self.assertFalse(client.is_configured())

    @override_settings(**GLPI_SETTINGS)
    def test_is_configured_true_com_credenciais(self):
        client = GlpiClient()
        self.assertTrue(client.is_configured())

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.get')
    def test_init_session_sucesso(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {'session_token': 'abc123'})
        mock_get.return_value.raise_for_status = lambda: None

        client = GlpiClient()
        token = client.init_session()
        self.assertEqual(token, 'abc123')
        self.assertEqual(client.session_token, 'abc123')

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.get')
    def test_init_session_falha_de_rede(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError('timeout')

        client = GlpiClient()
        with self.assertRaises(GlpiIntegrationError):
            client.init_session()

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.post')
    def test_create_ticket_sucesso(self, mock_post):
        mock_post.return_value = Mock(status_code=201, json=lambda: {'id': 42})
        mock_post.return_value.raise_for_status = lambda: None

        client = GlpiClient()
        client.session_token = 'abc123'
        ticket_id = client.create_ticket('Erro no login', 'descrição', 'Sistema', 'Alta')
        self.assertEqual(ticket_id, 42)

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.post')
    def test_create_ticket_sem_id_retornado_gera_erro(self, mock_post):
        mock_post.return_value = Mock(status_code=200, json=lambda: {})
        mock_post.return_value.raise_for_status = lambda: None

        client = GlpiClient()
        client.session_token = 'abc123'
        with self.assertRaises(GlpiIntegrationError):
            client.create_ticket('Erro no login', 'descrição', 'Sistema', 'Alta')


class EnviarChamadoGlpiTests(TestCase):
    def test_sem_configuracao_usa_mock(self):
        resultado = enviar_chamado_glpi('Erro no login', 'descrição', 'Sistema', 'Alta')
        self.assertEqual(resultado['origem'], 'mock')
        self.assertIsNone(resultado['erro'])
        self.assertTrue(resultado['id_glpi'].isdigit())

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.get')
    @patch('core.glpi_client.requests.post')
    def test_com_configuracao_e_api_disponivel_usa_real(self, mock_post, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {'session_token': 'abc123'})
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value = Mock(status_code=201, json=lambda: {'id': 99})
        mock_post.return_value.raise_for_status = lambda: None

        resultado = enviar_chamado_glpi('Erro no login', 'descrição', 'Sistema', 'Alta')
        self.assertEqual(resultado['origem'], 'real')
        self.assertEqual(resultado['id_glpi'], 99)
        self.assertIsNone(resultado['erro'])

    @override_settings(**GLPI_SETTINGS)
    @patch('core.glpi_client.requests.get')
    def test_com_configuracao_mas_api_indisponivel_cai_no_mock(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError('falha de rede')

        resultado = enviar_chamado_glpi('Erro no login', 'descrição', 'Sistema', 'Alta')
        self.assertEqual(resultado['origem'], 'mock')
        self.assertIsNotNone(resultado['erro'])
