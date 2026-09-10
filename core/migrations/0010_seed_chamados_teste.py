import random

from django.db import migrations


USUARIO = '03'
AREA = 'Engenharia'

CHAMADOS = [
    (
        'Erro ao gerar relatório de produção',
        'Ao clicar em "Gerar relatório", o sistema trava e nada acontece. Já tentei em '
        'dois computadores diferentes.',
        'Sistema',
        'Alta',
        'Novo',
    ),
    (
        'Solicito acesso à pasta compartilhada de projetos',
        'Preciso de acesso de leitura/escrita à pasta \\\\servidor\\projetos-engenharia para '
        'colaborar com a equipe.',
        'Acesso',
        'Media',
        'Em atendimento',
    ),
    (
        'Impressora do setor de engenharia não imprime em A3',
        'A impressora está configurada só para A4. Precisamos imprimir plantas em A3 com urgência.',
        'Equipamento',
        'Urgente',
        'Em atendimento',
    ),
    (
        'Notebook não conecta no Wi-Fi da fábrica',
        'O notebook conecta normalmente em casa, mas não reconhece a rede Wi-Fi da fábrica '
        'desde ontem.',
        'Equipamento',
        'Media',
        'Resolvido',
    ),
    (
        'Dúvida sobre licença do software de CAD',
        'Gostaria de saber se a licença do software de desenho técnico cobre o uso em notebook pessoal.',
        'Outros',
        'Baixa',
        'Cancelado',
    ),
]


def criar_chamados_teste(apps, schema_editor):
    Chamado = apps.get_model('core', 'Chamado')
    for titulo, descricao, categoria, prioridade, status in CHAMADOS:
        if Chamado.objects.filter(titulo=titulo).exists():
            continue
        Chamado.objects.create(
            titulo=titulo,
            descricao=descricao,
            categoria=categoria,
            prioridade=prioridade,
            usuario=USUARIO,
            area=AREA,
            status=status,
            id_glpi=str(random.randint(1000, 9999)),
        )


def remover_chamados_teste(apps, schema_editor):
    Chamado = apps.get_model('core', 'Chamado')
    Chamado.objects.filter(titulo__in=[c[0] for c in CHAMADOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_seed_projetos_teste'),
    ]

    operations = [
        migrations.RunPython(criar_chamados_teste, remover_chamados_teste),
    ]
