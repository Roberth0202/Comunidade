from django import forms
from .services import validate_password

class SolicitacaoRedefinicaoSenhaForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu email.'})
    )
    
class RedefinicaoSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua nova senha.'}),
        strip=False,
    )
    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme sua nova senha.'}),
        strip=False,
    )
    
    # método para validar os dados do formulário
    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get("nova_senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if nova_senha and confirmar_senha:
            if nova_senha != confirmar_senha:
                raise forms.ValidationError("As senhas não coincidem.")
            
            # valida a senha de acordo com as regras definidas
            try:
                validate_password(nova_senha)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
