from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Chamado, Perfil, Projeto


class AuthAndFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario',
            email='usuario@email.com',
            password='senha123',
        )

    def test_login_page_is_accessible(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_login_and_access_dashboard(self):
        response = self.client.post(reverse('login'), {
            'email': 'usuario@email.com',
            'password': 'senha123',
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('dashboard'))

    def test_can_create_called_with_required_fields(self):
        self.client.login(username='usuario', password='senha123')
        response = self.client.post(reverse('chamado_create'), {
            'titulo': 'Erro no login',
            'descricao': 'Problema ao acessar sistema',
            'categoria': 'Sistema',
            'prioridade': 'Alta',
        })
        self.assertEqual(response.status_code, 302)
        chamado = Chamado.objects.get(titulo='Erro no login')
        self.assertEqual(chamado.usuario, 'usuario')
        self.assertEqual(chamado.status, 'Novo')
        self.assertIsNotNone(chamado.id_glpi)

    def test_chamado_form_rejects_empty_description(self):
        self.client.login(username='usuario', password='senha123')
        response = self.client.post(reverse('chamado_create'), {
            'titulo': 'Chamado sem descrição',
            'descricao': '',
            'categoria': 'Sistema',
            'prioridade': 'Alta',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Chamado.objects.filter(titulo='Chamado sem descrição').exists())

    def test_can_create_project_with_required_fields(self):
        self.client.login(username='usuario', password='senha123')
        response = self.client.post(reverse('projeto_create'), {
            'titulo': 'Automatizar importação',
            'area_solicitante': 'TI',
            'descricao_problema': 'Processo manual lento',
            'objetivo': 'Reduzir esforço manual',
            'prioridade': 'Media',
        })
        self.assertEqual(response.status_code, 302)
        projeto = Projeto.objects.get(titulo='Automatizar importação')
        self.assertEqual(projeto.status, 'Novo')


class PapelPermissaoTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.colaborador = User.objects.create_user(username='colab1', password='senha123')
        Perfil.objects.create(user=self.colaborador, papel=Perfil.PAPEL_COLABORADOR, area='Qualidade')

        self.gestor = User.objects.create_user(username='gestor1', password='senha123')
        Perfil.objects.create(user=self.gestor, papel=Perfil.PAPEL_GESTOR, area='TI')

        self.gestor_ti = User.objects.create_user(username='ti1', password='senha123')
        Perfil.objects.create(user=self.gestor_ti, papel=Perfil.PAPEL_GESTOR_TI, area='')

        self.atendente_ti = User.objects.create_user(username='atd1', password='senha123')
        Perfil.objects.create(user=self.atendente_ti, papel=Perfil.PAPEL_COLABORADOR, area='TI')

        self.chamado_ti = Chamado.objects.create(
            titulo='Chamado da área TI', descricao='desc', categoria='Sistema',
            prioridade='Alta', usuario='colab1', area='TI',
        )
        self.chamado_outra_area = Chamado.objects.create(
            titulo='Chamado de outra área', descricao='desc', categoria='Sistema',
            prioridade='Alta', usuario='outro', area='Qualidade',
        )

    def test_colaborador_ve_apenas_os_proprios_chamados(self):
        self.client.login(username='colab1', password='senha123')
        response = self.client.get(reverse('chamados'))
        self.assertContains(response, 'Chamado da área TI')
        self.assertNotContains(response, 'Chamado de outra área')

    def test_gestor_ve_apenas_chamados_da_propria_area(self):
        self.client.login(username='gestor1', password='senha123')
        response = self.client.get(reverse('chamados'))
        self.assertContains(response, 'Chamado da área TI')
        self.assertNotContains(response, 'Chamado de outra área')

    def test_atendente_ti_ve_todos_os_chamados(self):
        self.client.login(username='atd1', password='senha123')
        response = self.client.get(reverse('chamados'))
        self.assertContains(response, 'Chamado da área TI')
        self.assertContains(response, 'Chamado de outra área')

    def test_atendente_ti_pode_pegar_chamado_da_esteira(self):
        self.client.login(username='atd1', password='senha123')
        response = self.client.post(reverse('chamado_pegar', args=[self.chamado_outra_area.pk]))
        self.assertEqual(response.status_code, 302)
        self.chamado_outra_area.refresh_from_db()
        self.assertEqual(self.chamado_outra_area.atendente, self.atendente_ti)
        self.assertEqual(self.chamado_outra_area.status, 'Em atendimento')

    def test_esteira_mostra_projetos_sem_atendimento(self):
        projeto = Projeto.objects.create(
            titulo='Projeto sem atendimento', area_solicitante='Qualidade',
            descricao_problema='desc', objetivo='obj', prioridade='Alta',
        )
        self.client.login(username='atd1', password='senha123')
        response = self.client.get(reverse('esteira'))
        self.assertContains(response, 'Projeto sem atendimento')
        self.assertIn(projeto, response.context['projetos'])

    def test_atendente_ti_pode_pegar_projeto_da_esteira(self):
        projeto = Projeto.objects.create(
            titulo='Projeto para pegar', area_solicitante='Qualidade',
            descricao_problema='desc', objetivo='obj', prioridade='Alta',
        )
        self.client.login(username='atd1', password='senha123')
        response = self.client.post(reverse('projeto_pegar', args=[projeto.pk]))
        self.assertEqual(response.status_code, 302)
        projeto.refresh_from_db()
        self.assertEqual(projeto.atendente, self.atendente_ti)
        self.assertEqual(projeto.status, 'Em análise')

    def test_colaborador_comum_nao_acessa_esteira(self):
        self.client.login(username='colab1', password='senha123')
        response = self.client.get(reverse('esteira'), follow=True)
        self.assertRedirects(response, reverse('dashboard'))

    def test_gestor_ti_ve_todos_os_chamados(self):
        self.client.login(username='ti1', password='senha123')
        response = self.client.get(reverse('chamados'))
        self.assertContains(response, 'Chamado da área TI')
        self.assertContains(response, 'Chamado de outra área')

    def test_dashboard_respeita_area_do_gestor(self):
        self.client.login(username='gestor1', password='senha123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total_chamados'], 1)
        self.assertContains(response, 'Chamado da área TI')
        self.assertNotContains(response, 'Chamado de outra área')

    def test_dashboard_gestor_ti_ve_total_geral(self):
        self.client.login(username='ti1', password='senha123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total_chamados'], Chamado.objects.count())

    def test_colaborador_nao_acessa_gestao_de_usuarios(self):
        self.client.login(username='colab1', password='senha123')
        response = self.client.get(reverse('usuarios'), follow=True)
        self.assertRedirects(response, reverse('dashboard'))

    def test_gestor_ti_pode_criar_usuario(self):
        self.client.login(username='ti1', password='senha123')
        response = self.client.post(reverse('usuario_create'), {
            'nome_completo': 'Maria Souza',
            'username': '000456',
            'email': 'novo@empresa.com',
            'papel': Perfil.PAPEL_GESTOR,
            'area': 'Qualidade',
        })
        self.assertEqual(response.status_code, 302)
        novo_perfil = Perfil.objects.get(user__username='000456', papel=Perfil.PAPEL_GESTOR)
        self.assertEqual(novo_perfil.user.first_name, 'Maria')
        self.assertEqual(novo_perfil.user.last_name, 'Souza')
        self.assertTrue(novo_perfil.user.check_password('000456'))

    def test_gestor_area_cria_colaborador_restrito_a_propria_area(self):
        self.client.login(username='gestor1', password='senha123')
        response = self.client.post(reverse('usuario_create'), {
            'nome_completo': 'Carlos Souza',
            'username': '000789',
            'email': 'carlos@empresa.com',
            'papel': Perfil.PAPEL_GESTOR,
            'area': 'Qualidade',
        })
        self.assertEqual(response.status_code, 302)
        novo_perfil = Perfil.objects.get(user__username='000789')
        self.assertEqual(novo_perfil.papel, Perfil.PAPEL_COLABORADOR)
        self.assertEqual(novo_perfil.area, 'TI')

    def test_matricula_deve_conter_apenas_numeros(self):
        self.client.login(username='ti1', password='senha123')
        response = self.client.post(reverse('usuario_create'), {
            'nome_completo': 'João Silva',
            'username': 'abc123',
            'email': 'joao@empresa.com',
            'papel': Perfil.PAPEL_COLABORADOR,
            'area': 'TI',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='abc123').exists())

    def test_gestor_pode_alterar_status_de_chamado_da_propria_area(self):
        self.client.login(username='gestor1', password='senha123')
        response = self.client.post(
            reverse('chamado_status_update', args=[self.chamado_ti.pk]),
            {'status': 'Em atendimento'},
        )
        self.assertEqual(response.status_code, 302)
        self.chamado_ti.refresh_from_db()
        self.assertEqual(self.chamado_ti.status, 'Em atendimento')

    def test_gestor_nao_pode_alterar_status_de_chamado_de_outra_area(self):
        self.client.login(username='gestor1', password='senha123')
        self.client.post(
            reverse('chamado_status_update', args=[self.chamado_outra_area.pk]),
            {'status': 'Resolvido'},
        )
        self.chamado_outra_area.refresh_from_db()
        self.assertEqual(self.chamado_outra_area.status, 'Novo')

    def test_project_detail_view_shows_full_data(self):
        self.client.login(username='colab1', password='senha123')
        projeto = Projeto.objects.create(
            titulo='Projeto X',
            area_solicitante='TI',
            descricao_problema='Descrição do problema',
            objetivo='Objetivo do projeto',
            prioridade='Alta',
        )
        response = self.client.get(reverse('projeto_detail', args=[projeto.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Projeto X')
        self.assertContains(response, 'Descrição do problema')
