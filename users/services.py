from .models import CustomUser, EmailVerificationToken
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.utils import timezone
from datetime import timedelta
from celery import shared_task

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
        is_valid = True
        
        # Verifica se as senhas são iguais
        if self.password1 != self.password2:
            messages.error(self.request, 'As senhas não coincidem', extra_tags='senhas_diferentes')
            is_valid = False
            return is_valid

        # Verifica se o nome de usuário já existe
        if CustomUser.objects.filter(username = self.username).exists():
            messages.error(self.request, 'O nome de usuário já está em uso.', extra_tags='usuario_existente')
            is_valid = False
            return is_valid
            
        # Verifica se o email já existe
        if CustomUser.objects.filter(email = self.email).exists():
            messages.error(self.request, 'O email já está em uso.', extra_tags='email_existente')
            is_valid = False
            return is_valid
    
        return is_valid

    # ====================================== Método para validar a senha ==========================================
    # Método para validar a senha
    def valid_password(self):
        # Obtém os validadores de senha configurados
        password_validators = get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
        
        try:
            # Valida a senha de acordo com as regras definidas
            validate_password(self.password1, password_validators = password_validators) # 
            
        except Exception as e:
            messages.error(self.request, str(e), extra_tags='erro_senha')
            return render(self.request, 'register.html')
        
        return True
        
    #====================================== Método para criar um novo usuário ===================================
    def create_user(self):
        # Cria um novo usuário inativo ate verificar email
        user = CustomUser.objects.create_user(
            username = self.username,
            password = self.password1,
            email = self.email,
            data_nascimento = self.data_nascimento,
            is_active = False, # Define o usuário como inativo inicialmente
            e_verificado = False, # Define o email como não verificado inicialmente
        )
        
        return user.save() # Confirma a transação e salva o usuário no banco de dados

    # ================================ Método para enviar email de verificação ===================================
    def send_email_verification(self, user):
        
        # invalida tokens antigos não usados
        EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Cria um novo token de verificação, user=user associa o token ao usuário
        token = EmailVerificationToken.objects.create(user=user)
        
        #URL de verificação
        verify_url = f'{settings.SITE_URL}/verify-email/{token.token}/'
        
        # rederiza o template de email
        html_content = render_to_string('email/verify_email.html', {
            'user': user,
            'verify_url': verify_url,
            'SITE_NAME' : settings.SITE_NAME,
        })
        
        # remove as tags HTML do conteúdo do email
        text_content = strip_tags(html_content)  
        
        try:
            # Envia o email de verificação
            send_mail(
                subject = f'Verifique seu email', # Assunto do email
                message = text_content, # Mensagem de texto do email
                from_email = settings.DEFAULT_FROM_EMAIL, # Email do remetente
                recipient_list = [user.email], # Lista de destinatários
                html_message = html_content # Mensagem HTML do email
            )
            return True
        
        except Exception as e:
            print(f'Erro ao enviar email de verificação: {e}')
            return False
        
    # ================================ Método para verificar o email ===================================
    

# função para deletar usuários não verificados depois de 7 dias
@shared_task # Transforma essa função em uma tarefa que pode ser executada em background
def deleta_usuarios_nao_verificado():
    
    # calcula uma data 7 dias atrás
    sete_dias_atras = timezone.now() - timedelta(days=7)
    
    # filtra os usuários que não verificaram o email e foram criados a mais de 7 dias   
    usuarios_nao_verificados = CustomUser.objects.filter(
        e_verificado=False, 
        data_criacao__lte = sete_dias_atras) # __lte = "less than or equal" (menor ou igual)
    
    count = usuarios_nao_verificados.count() # conta quantos usuários serão deletados
    usuarios_nao_verificados.delete()
    return f'Deletados {count} usuários não verificados.'
    
    