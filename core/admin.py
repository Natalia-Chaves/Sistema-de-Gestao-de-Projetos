from django.contrib import admin

from .models import Chamado, Perfil, Projeto


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'papel', 'area')
    list_filter = ('papel', 'area')
    search_fields = ('user__username',)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'prioridade', 'status', 'usuario', 'data_criacao')
    list_filter = ('status', 'categoria', 'prioridade')
    search_fields = ('titulo', 'descricao', 'usuario')


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'area_solicitante', 'prioridade', 'status', 'data_criacao')
    list_filter = ('status', 'prioridade')
    search_fields = ('titulo', 'area_solicitante', 'descricao_problema')
