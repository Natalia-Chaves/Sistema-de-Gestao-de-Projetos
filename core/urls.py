from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chamados/', views.chamados_view, name='chamados'),
    path('chamados/novo/', views.chamado_create_view, name='chamado_create'),
    path('chamados/<int:pk>/', views.chamado_detail_view, name='chamado_detail'),
    path('projetos/', views.projetos_view, name='projetos'),
    path('projetos/novo/', views.projeto_create_view, name='projeto_create'),
    path('projetos/<int:pk>/', views.projeto_detail_view, name='projeto_detail'),
    path('chamados/<int:pk>/status/', views.chamado_status_update_view, name='chamado_status_update'),
    path('projetos/<int:pk>/status/', views.projeto_status_update_view, name='projeto_status_update'),
    path('esteira/', views.esteira_view, name='esteira'),
    path('esteira/chamados/<int:pk>/pegar/', views.chamado_pegar_view, name='chamado_pegar'),
    path('esteira/projetos/<int:pk>/pegar/', views.projeto_pegar_view, name='projeto_pegar'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('usuarios/novo/', views.usuario_create_view, name='usuario_create'),
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),
]
