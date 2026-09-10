from django.db import migrations


AREA = 'Engenharia'

PROJETOS = [
    (
        'Automatizar geração de relatórios semanais',
        'A equipe gasta cerca de 6 horas por semana consolidando planilhas manualmente '
        'para gerar o relatório semanal de produção.',
        'Criar um script/robô que consolide os dados automaticamente e envie o relatório por e-mail.',
        'Alta',
        'Redução de ~6h/semana de trabalho manual e menos erros de digitação.',
        'Novo',
    ),
    (
        'Integração do sistema de estoque com o ERP',
        'O controle de estoque de peças é feito em planilha separada do ERP, causando '
        'divergências frequentes entre o saldo real e o sistema.',
        'Integrar a planilha de estoque diretamente ao ERP via API, eliminando o retrabalho manual.',
        'Alta',
        'Estoque sempre atualizado e eliminação de divergências de inventário.',
        'Em análise',
    ),
    (
        'Dashboard de indicadores de manutenção',
        'Não existe um painel único para acompanhar chamados de manutenção, tempo médio '
        'de atendimento e equipamentos com mais ocorrências.',
        'Desenvolver um dashboard com os principais indicadores de manutenção em tempo real.',
        'Media',
        'Visibilidade gerencial para priorizar manutenções preventivas.',
        'Aprovado',
    ),
    (
        'App interno para apontamento de horas em campo',
        'Os técnicos de campo preenchem o apontamento de horas em papel, que depois é '
        'digitado manualmente pelo setor administrativo.',
        'Criar um aplicativo simples para apontamento de horas direto pelo celular.',
        'Media',
        'Elimina a redigitação e reduz erros de lançamento de horas.',
        'Em desenvolvimento',
    ),
    (
        'Padronização de templates de desenho técnico',
        'Cada engenheiro usa um layout diferente de desenho técnico, dificultando a '
        'revisão e o arquivamento padronizado dos projetos.',
        'Criar templates padronizados e treinar a equipe para uso obrigatório.',
        'Baixa',
        'Desenhos mais consistentes e fáceis de revisar/arquivar.',
        'Concluído',
    ),
]


def criar_projetos_teste(apps, schema_editor):
    Projeto = apps.get_model('core', 'Projeto')
    for titulo, descricao_problema, objetivo, prioridade, beneficio_esperado, status in PROJETOS:
        if Projeto.objects.filter(titulo=titulo).exists():
            continue
        Projeto.objects.create(
            titulo=titulo,
            area_solicitante=AREA,
            descricao_problema=descricao_problema,
            objetivo=objetivo,
            prioridade=prioridade,
            beneficio_esperado=beneficio_esperado,
            status=status,
        )


def remover_projetos_teste(apps, schema_editor):
    Projeto = apps.get_model('core', 'Projeto')
    Projeto.objects.filter(titulo__in=[p[0] for p in PROJETOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_seed_usuarios_teste'),
    ]

    operations = [
        migrations.RunPython(criar_projetos_teste, remover_projetos_teste),
    ]
