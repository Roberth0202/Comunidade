from .models import CustomUser
from django.contrib import messages
from django.shortcuts import render, redirect
from comuna.settings import AUTH_PASSWORD_VALIDATORS
from django.contrib.auth.password_validation import validate_password, get_password_validators

# criar um objeto validador de registro de usuario 
class RegisterUser:
    def __init__(self, request, username, email, password1, password2, data_nascimento):
        self.username = username
        self.email = email
        self.password1 = password1
        self.password2 = password2
        self.data_nascimento = data_nascimento
        self.request = request
    
    # Método para validar os dados do usuário
    def is_valid(self):
        # Verifica se as senhas são iguais
        if self.password1 != self.password2:
            messages.error(self.request, 'As senhas não coincidem', extra_tags='senhas_diferentes')
            return render(self.request, 'users/register.html')

        # Verifica se o nome de usuário já existe
        if CustomUser.objects.filter(username=self.username).exists():
            messages.error(self.request, 'O nome de usuário já está em uso', extra_tags='usuario_existente')
            return render(self.request, 'users/register.html')

        # Verifica se o email já existe
        if CustomUser.objects.filter(email=self.email).exists():
            messages.error(self.request, 'O email já está em uso', extra_tags='email_existente')
            return render(self.request, 'users/register.html')
        return True

    # Método para validar a senha
    def valid_password(self):
        # Obtém os validadores de senha configurados
        password_validators = get_password_validators(AUTH_PASSWORD_VALIDATORS)
        
        try:
            # Valida a senha de acordo com as regras definidas
            validate_password(self.password1, user=None, password_validators=password_validators)
        except Exception as e:
            messages.error(self.request, str(e), extra_tags='erro_senha')
            return render(self.request, 'users/register.html')
        
        return True
        
    # Método para criar um novo usuário
    def create_user(self):
        # Cria um novo usuário
        user = CustomUser.objects.create_user(
            username=self.username,
            password=self.password1,
            email=self.email,
            data_nascimento=self.data_nascimento
        )
        user.save()
        messages.success(self.request, 'Usuário criado com sucesso!', extra_tags='usuario_criado')
        return redirect('login/')