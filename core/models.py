from django.conf import settings
from django.db import models

AREA_CHOICES = [
    ('Engenharia', 'Engenharia'),
    ('Producao', 'Produção'),
    ('Manutencao', 'Manutenção'),
    ('Qualidade', 'Qualidade'),
    ('Suprimentos', 'Suprimentos'),
    ('Administrativo', 'Administrativo'),
    ('TI', 'TI'),
]


class Perfil(models.Model):
    PAPEL_COLABORADOR = 'colaborador'
    PAPEL_GESTOR = 'gestor'
    PAPEL_GESTOR_TI = 'gestor_ti'
    PAPEL_CHOICES = [
        (PAPEL_COLABORADOR, 'Colaborador'),
        (PAPEL_GESTOR, 'Gestor de área'),
        (PAPEL_GESTOR_TI, 'Gestor de Desenvolvimento'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default=PAPEL_COLABORADOR)
    area = models.CharField(max_length=50, choices=AREA_CHOICES, blank=True)
    senha_temporaria = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} ({self.get_papel_display()})'


class Chamado(models.Model):
    STATUS_CHOICES = [
        ('Novo', 'Novo'),
        ('Em atendimento', 'Em atendimento'),
        ('Resolvido', 'Resolvido'),
        ('Cancelado', 'Cancelado'),
    ]

    CATEGORIA_CHOICES = [
        ('Sistema', 'Sistema'),
        ('Acesso', 'Acesso'),
        ('Equipamento', 'Equipamento'),
        ('Outros', 'Outros'),
    ]

    PRIORIDADE_CHOICES = [
        ('Baixa', 'Baixa'),
        ('Media', 'Média'),
        ('Alta', 'Alta'),
        ('Urgente', 'Urgente'),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField()
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES, default='Sistema')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='Media')
    usuario = models.CharField(max_length=150, db_index=True)
    area = models.CharField(max_length=50, choices=AREA_CHOICES, blank=True, db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Novo', db_index=True)
    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chamados_atendidos',
    )
    id_glpi = models.CharField(max_length=100, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo


class Projeto(models.Model):
    STATUS_CHOICES = [
        ('Novo', 'Novo'),
        ('Em análise', 'Em análise'),
        ('Aprovado', 'Aprovado'),
        ('Em desenvolvimento', 'Em desenvolvimento'),
        ('Concluído', 'Concluído'),
    ]

    PRIORIDADE_CHOICES = [
        ('Baixa', 'Baixa'),
        ('Media', 'Média'),
        ('Alta', 'Alta'),
    ]

    titulo = models.CharField(max_length=150)
    area_solicitante = models.CharField(max_length=50, choices=AREA_CHOICES, db_index=True)
    descricao_problema = models.TextField()
    objetivo = models.TextField()
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='Media')
    beneficio_esperado = models.TextField(blank=True, null=True)
    prazo_desejado = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Novo', db_index=True)
    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projetos_atendidos',
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo
