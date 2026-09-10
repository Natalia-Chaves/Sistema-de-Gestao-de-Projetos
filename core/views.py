from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from .forms import AlterarSenhaForm, ChamadoForm, LoginForm, ProjetoForm, UsuarioForm
from .models import Chamado, Perfil, Projeto
from .permissions import atendente_required, eh_colaborador_ti, get_perfil, gestor_ou_ti_required, status_required
from .services import enviar_chamado_glpi

MAX_TENTATIVAS_LOGIN = 5
BLOQUEIO_LOGIN_SEGUNDOS = 300


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            chave_bloqueio = f'login_bloqueado:{email}'
            chave_tentativas = f'login_tentativas:{email}'

            if cache.get(chave_bloqueio):
                messages.error(
                    request,
                    'Muitas tentativas de login incorretas. Tente novamente em alguns minutos.',
                )
                return render(request, 'core/login.html', {'form': form})

            usuario_encontrado = User.objects.filter(email__iexact=email).first()
            username_para_autenticar = usuario_encontrado.username if usuario_encontrado else email
            user = authenticate(
                request,
                username=username_para_autenticar,
                password=form.cleaned_data['password'],
            )
            if user is not None:
                cache.delete(chave_tentativas)
                login(request, user)
                messages.success(request, 'Login realizado com sucesso.')
                return redirect('dashboard')

            tentativas = cache.get(chave_tentativas, 0) + 1
            cache.set(chave_tentativas, tentativas, BLOQUEIO_LOGIN_SEGUNDOS)
            if tentativas >= MAX_TENTATIVAS_LOGIN:
                cache.set(chave_bloqueio, True, BLOQUEIO_LOGIN_SEGUNDOS)
                messages.error(
                    request,
                    'Muitas tentativas de login incorretas. Tente novamente em alguns minutos.',
                )
            else:
                messages.error(request, 'Credenciais inválidas.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def alterar_senha_view(request):
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['nova_senha'])
            request.user.save()
            perfil = get_perfil(request.user)
            if perfil.pk:
                perfil.senha_temporaria = False
                perfil.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha alterada com sucesso.')
            return redirect('dashboard')
    else:
        form = AlterarSenhaForm(request.user)
    return render(request, 'core/alterar_senha.html', {'form': form})



@login_required(login_url='login')
def dashboard_view(request):
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR_TI or eh_colaborador_ti(perfil):
        chamados_qs = Chamado.objects.all()
        projetos_qs = Projeto.objects.all()
    elif perfil.papel == Perfil.PAPEL_GESTOR:
        chamados_qs = Chamado.objects.filter(area=perfil.area)
        projetos_qs = Projeto.objects.filter(area_solicitante=perfil.area)
    else:
        chamados_qs = Chamado.objects.filter(usuario=request.user.username)
        projetos_qs = Projeto.objects.all()

    chamados = chamados_qs.order_by('-data_criacao')[:5]
    projetos = projetos_qs.order_by('-data_criacao')[:5]

    chamados_por_status = dict(chamados_qs.values_list('status').annotate(total=Count('id')))
    projetos_por_status = dict(projetos_qs.values_list('status').annotate(total=Count('id')))
    chamados_status_lista = [
        (label, chamados_por_status.get(value, 0)) for value, label in Chamado.STATUS_CHOICES
    ]
    projetos_status_lista = [
        (label, projetos_por_status.get(value, 0)) for value, label in Projeto.STATUS_CHOICES
    ]

    contexto = {
        'total_chamados': chamados_qs.count(),
        'total_projetos': projetos_qs.count(),
        'chamados': chamados,
        'projetos': projetos,
        'chamados_status_lista': chamados_status_lista,
        'projetos_status_lista': projetos_status_lista,
    }
    return render(request, 'core/dashboard.html', contexto)


@login_required(login_url='login')
def chamados_view(request):
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR_TI or eh_colaborador_ti(perfil):
        objetos = Chamado.objects.all()
    elif perfil.papel == Perfil.PAPEL_GESTOR:
        objetos = Chamado.objects.filter(area=perfil.area)
    else:
        objetos = Chamado.objects.filter(usuario=request.user.username)

    texto = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    prioridade = request.GET.get('prioridade', '').strip()
    if texto:
        objetos = objetos.filter(Q(titulo__icontains=texto) | Q(descricao__icontains=texto))
    status_validos = {value for value, _ in Chamado.STATUS_CHOICES}
    prioridades_validas = {value for value, _ in Chamado.PRIORIDADE_CHOICES}
    if status in status_validos:
        objetos = objetos.filter(status=status)
    else:
        status = ''
    if prioridade in prioridades_validas:
        objetos = objetos.filter(prioridade=prioridade)
    else:
        prioridade = ''

    objetos = objetos.order_by('-data_criacao')
    pagina = Paginator(objetos, 10).get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)
    contexto = {
        'chamados': pagina,
        'page_obj': pagina,
        'query_string': query_params.urlencode(),
        'status_choices': Chamado.STATUS_CHOICES,
        'prioridade_choices': Chamado.PRIORIDADE_CHOICES,
        'filtro_q': texto,
        'filtro_status': status,
        'filtro_prioridade': prioridade,
    }
    return render(request, 'core/chamados.html', contexto)


@login_required(login_url='login')
def chamado_detail_view(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR_TI or eh_colaborador_ti(perfil):
        return render(request, 'core/chamado_detail.html', {'chamado': chamado})
    if perfil.papel == Perfil.PAPEL_GESTOR and chamado.area != perfil.area:
        messages.error(request, 'Você só pode visualizar chamados da sua área.')
        return redirect('chamados')
    if perfil.papel == Perfil.PAPEL_COLABORADOR and chamado.usuario != request.user.username:
        messages.error(request, 'Você só pode visualizar os próprios chamados.')
        return redirect('chamados')
    return render(request, 'core/chamado_detail.html', {'chamado': chamado})


@login_required(login_url='login')
def chamado_create_view(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.usuario = request.user.username
            chamado.area = get_perfil(request.user).area
            resultado = enviar_chamado_glpi(
                chamado.titulo, chamado.descricao, chamado.categoria, chamado.prioridade
            )
            chamado.id_glpi = resultado.get('id_glpi')
            chamado.save()
            messages.success(request, 'Chamado registrado com sucesso.')
            return redirect('chamados')
    else:
        form = ChamadoForm()
    return render(request, 'core/chamado_form.html', {'form': form, 'title': 'Abrir chamado'})


@login_required(login_url='login')
def projetos_view(request):
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR_TI:
        objetos = Projeto.objects.all()
    elif perfil.papel == Perfil.PAPEL_GESTOR:
        objetos = Projeto.objects.filter(area_solicitante=perfil.area)
    else:
        objetos = Projeto.objects.all()

    texto = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    prioridade = request.GET.get('prioridade', '').strip()
    if texto:
        objetos = objetos.filter(Q(titulo__icontains=texto) | Q(descricao_problema__icontains=texto))
    status_validos = {value for value, _ in Projeto.STATUS_CHOICES}
    prioridades_validas = {value for value, _ in Projeto.PRIORIDADE_CHOICES}
    if status in status_validos:
        objetos = objetos.filter(status=status)
    else:
        status = ''
    if prioridade in prioridades_validas:
        objetos = objetos.filter(prioridade=prioridade)
    else:
        prioridade = ''

    objetos = objetos.order_by('-data_criacao')
    pagina = Paginator(objetos, 10).get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)
    contexto = {
        'projetos': pagina,
        'page_obj': pagina,
        'query_string': query_params.urlencode(),
        'status_choices': Projeto.STATUS_CHOICES,
        'prioridade_choices': Projeto.PRIORIDADE_CHOICES,
        'filtro_q': texto,
        'filtro_status': status,
        'filtro_prioridade': prioridade,
    }
    return render(request, 'core/projetos.html', contexto)


@login_required(login_url='login')
def projeto_detail_view(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR and projeto.area_solicitante != perfil.area:
        messages.error(request, 'Você só pode visualizar projetos da sua área.')
        return redirect('projetos')
    return render(request, 'core/projeto_detail.html', {'projeto': projeto})


@login_required(login_url='login')
def projeto_create_view(request):
    perfil = get_perfil(request.user)
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            if perfil.papel != Perfil.PAPEL_GESTOR_TI and perfil.area:
                projeto.area_solicitante = perfil.area
            projeto.save()
            messages.success(request, 'Projeto registrado com sucesso.')
            return redirect('projetos')
    else:
        initial = {'area_solicitante': perfil.area} if perfil.area else {}
        form = ProjetoForm(initial=initial)
    return render(request, 'core/projeto_form.html', {'form': form, 'title': 'Abrir projeto'})


@login_required(login_url='login')
@status_required
def chamado_status_update_view(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR and chamado.area != perfil.area:
        messages.error(request, 'Você só pode alterar chamados da sua área.')
        return redirect('chamados')
    novo_status = request.POST.get('status')
    if novo_status in dict(Chamado.STATUS_CHOICES):
        chamado.status = novo_status
        chamado.save()
        messages.success(request, 'Status do chamado atualizado.')
    return redirect('chamados')


@login_required(login_url='login')
@atendente_required
def esteira_view(request):
    chamados = Chamado.objects.filter(atendente__isnull=True, status='Novo').order_by('data_criacao')
    projetos = Projeto.objects.filter(atendente__isnull=True, status='Novo').order_by('data_criacao')
    return render(request, 'core/esteira.html', {'chamados': chamados, 'projetos': projetos})


@login_required(login_url='login')
@atendente_required
def chamado_pegar_view(request, pk):
    atualizado = Chamado.objects.filter(pk=pk, atendente__isnull=True).update(
        atendente=request.user, status='Em atendimento', data_atualizacao=timezone.now(),
    )
    if atualizado:
        messages.success(request, 'Chamado atribuído a você.')
    else:
        messages.error(request, 'Esse chamado já foi atribuído a outro atendente.')
    return redirect('esteira')


@login_required(login_url='login')
@atendente_required
def projeto_pegar_view(request, pk):
    atualizado = Projeto.objects.filter(pk=pk, atendente__isnull=True).update(
        atendente=request.user, status='Em análise', data_atualizacao=timezone.now(),
    )
    if atualizado:
        messages.success(request, 'Projeto atribuído a você.')
    else:
        messages.error(request, 'Esse projeto já foi atribuído a outro atendente.')
    return redirect('esteira')


@login_required(login_url='login')
@status_required
def projeto_status_update_view(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    perfil = get_perfil(request.user)
    if perfil.papel == Perfil.PAPEL_GESTOR and projeto.area_solicitante != perfil.area:
        messages.error(request, 'Você só pode alterar projetos da sua área.')
        return redirect('projetos')
    novo_status = request.POST.get('status')
    if novo_status in dict(Projeto.STATUS_CHOICES):
        projeto.status = novo_status
        projeto.save()
        messages.success(request, 'Status do projeto atualizado.')
    return redirect('projetos')


@login_required(login_url='login')
@gestor_ou_ti_required
def usuarios_view(request):
    perfil = get_perfil(request.user)
    perfis = Perfil.objects.exclude(papel=Perfil.PAPEL_GESTOR_TI).select_related('user')
    if perfil.papel == Perfil.PAPEL_GESTOR:
        perfis = perfis.filter(area=perfil.area)
    return render(request, 'core/usuarios.html', {'perfis': perfis})


@login_required(login_url='login')
@gestor_ou_ti_required
def usuario_create_view(request):
    perfil = get_perfil(request.user)
    area_fixa = perfil.area if perfil.papel == Perfil.PAPEL_GESTOR else None
    if request.method == 'POST':
        form = UsuarioForm(request.POST, area_fixa=area_fixa)
        if form.is_valid():
            nome_completo = form.cleaned_data['nome_completo'].strip()
            primeiro_nome, _, sobrenome = nome_completo.partition(' ')
            matricula = form.cleaned_data['username']
            papel = Perfil.PAPEL_COLABORADOR if area_fixa else form.cleaned_data['papel']
            area = area_fixa or form.cleaned_data['area']
            user = User.objects.create_user(
                username=matricula,
                email=form.cleaned_data['email'],
                password=matricula,
                first_name=primeiro_nome,
                last_name=sobrenome,
            )
            Perfil.objects.create(
                user=user,
                papel=papel,
                area=area,
                senha_temporaria=True,
            )
            messages.success(
                request,
                f'Usuário criado com sucesso. A senha inicial é a própria matrícula ({matricula}) '
                'e será solicitada a troca no primeiro acesso.',
            )
            return redirect('usuarios')
    else:
        form = UsuarioForm(area_fixa=area_fixa)
    return render(request, 'core/usuario_form.html', {'form': form, 'title': 'Novo usuário'})
