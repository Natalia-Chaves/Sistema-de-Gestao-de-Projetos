from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations


USUARIOS = [
    ('01', 'gestorti@empresa.com', 'gestor_ti', ''),
    ('02', 'atendenteti@empresa.com', 'colaborador', 'TI'),
    ('03', 'gestorengenharia@empresa.com', 'gestor', 'Engenharia'),
]


def criar_usuarios_teste(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Perfil = apps.get_model('core', 'Perfil')

    for matricula, email, papel, area in USUARIOS:
        if User.objects.filter(username=matricula).exists():
            continue
        user = User.objects.create(
            username=matricula, email=email, is_active=True, password=make_password(matricula),
        )
        Perfil.objects.create(user=user, papel=papel, area=area, senha_temporaria=True)


def remover_usuarios_teste(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    User.objects.filter(username__in=[u[0] for u in USUARIOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_chamado_atendente'),
    ]

    operations = [
        migrations.RunPython(criar_usuarios_teste, remover_usuarios_teste),
    ]
