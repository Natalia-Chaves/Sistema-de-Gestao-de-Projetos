from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Chamado, Perfil, Projeto

INPUT_CLASS = 'w-full border border-border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary'


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
    )


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'descricao', 'categoria', 'prioridade']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT_CLASS, 'maxlength': 150}),
            'descricao': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'categoria': forms.Select(attrs={'class': INPUT_CLASS}),
            'prioridade': forms.Select(attrs={'class': INPUT_CLASS}),
        }


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = [
            'titulo',
            'area_solicitante',
            'descricao_problema',
            'objetivo',
            'prioridade',
            'beneficio_esperado',
            'prazo_desejado',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'area_solicitante': forms.Select(attrs={'class': INPUT_CLASS}),
            'descricao_problema': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'objetivo': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
            'prioridade': forms.Select(attrs={'class': INPUT_CLASS}),
            'beneficio_esperado': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
            'prazo_desejado': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
        }


class UsuarioForm(forms.Form):
    nome_completo = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS}),
    )
    username = forms.CharField(
        label='Matrícula',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: 000123', 'inputmode': 'numeric'}),
    )
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': INPUT_CLASS}))
    papel = forms.ChoiceField(
        label='Papel',
        choices=[
            (Perfil.PAPEL_COLABORADOR, 'Colaborador'),
            (Perfil.PAPEL_GESTOR, 'Gestor de área'),
        ],
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )
    area = forms.ChoiceField(
        label='Área',
        choices=Perfil._meta.get_field('area').choices,
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )

    def __init__(self, *args, area_fixa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if area_fixa:
            self.fields['papel'].choices = [(Perfil.PAPEL_COLABORADOR, 'Colaborador')]
            self.fields['papel'].initial = Perfil.PAPEL_COLABORADOR
            self.fields['papel'].widget.attrs['disabled'] = True
            self.fields['area'].choices = [(area_fixa, dict(Perfil._meta.get_field('area').choices).get(area_fixa, area_fixa))]
            self.fields['area'].initial = area_fixa
            self.fields['area'].widget.attrs['disabled'] = True

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username.isdigit():
            raise forms.ValidationError('A matrícula deve conter apenas números.')
        from django.contrib.auth import get_user_model
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError('Já existe um usuário com essa matrícula.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        from django.contrib.auth import get_user_model
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe um usuário com esse e-mail.')
        return email


class AlterarSenhaForm(forms.Form):
    senha_atual = forms.CharField(label='Senha atual', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))
    nova_senha = forms.CharField(label='Nova senha', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))
    confirmar_senha = forms.CharField(label='Confirmar nova senha', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_senha_atual(self):
        senha_atual = self.cleaned_data['senha_atual']
        if not self.user.check_password(senha_atual):
            raise forms.ValidationError('Senha atual incorreta.')
        return senha_atual

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            raise forms.ValidationError('As senhas não coincidem.')
        if nova_senha:
            try:
                validate_password(nova_senha, user=self.user)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return cleaned_data

