from django import forms
from django.core.exceptions import ValidationError
from .services import validate_password_strength as validate_password
from .models import CustomUser
import cloudinary

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
                self.add_error('confirmar_senha', "As senhas não coincidem.")
            else:
                # valida a senha de acordo com as regras definidas
                try:
                    validate_password(nova_senha)
                except ValidationError as e:
                    self.add_error('nova_senha', e)
        
        return cleaned_data

class EditUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['capa', 'avatar', 'username', 'bio']
        widgets = {
            'capa': forms.ClearableFileInput(attrs={'class': ' form-control-file'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário', 'maxlength': 20}),
            'bio': forms.Textarea( attrs={'class': 'form-control', 'maxlength': 160,'placeholder': 'Bio', }),
        }
        help_texts = {
            'username': '',
        }
        error_messages = {
            'username': {
                'invalid': 'Nome de usuário inválido. Use apenas letras, números, espaços e @/./+/-/_',
                'unique': 'Um usuário com este nome já existe.',
            },
        }

    def save(self, commit=True):
        # Primeiro, obtemos o estado antigo do usuário do banco de dados
        old_user = CustomUser.objects.get(pk=self.instance.pk)

        # Em seguida, chamamos o método save do pai com commit=False para que o upload seja feito,
        # mas o objeto não seja salvo no banco de dados ainda.
        user = super().save(commit=False)

        # Agora, verificamos se o campo 'avatar' foi alterado.
        if 'avatar' in self.changed_data:
            # Se havia um avatar antigo, nós o deletamos.
            if old_user.avatar and hasattr(old_user.avatar, 'public_id'):
                cloudinary.uploader.destroy(old_user.avatar.public_id)

        # Fazemos o mesmo para o campo 'capa'.
        if 'capa' in self.changed_data:
            # Se havia uma capa antiga, nós a deletamos.
            if old_user.capa and hasattr(old_user.capa, 'public_id'):
                cloudinary.uploader.destroy(old_user.capa.public_id)

        if commit:
            user.save()

        return user