from .models import CustomUser, EmailVerificationToken, Follow
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
import cloudinary.uploader

import re


# ====================================== Validação de Senha (Refatorado) =======================================
def validate_password_strength(password):
    """
    Executa uma série de validações de força da senha.
    Levanta ValidationError em caso de falha.
    """
    if not password:
        raise ValidationError('A senha é obrigatória.', code='senha_vazia')
    
    if len(password) < 8:
        raise ValidationError('A senha deve ter pelo menos 8 caracteres.', code='senha_curta')
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>/?]', password):
        raise ValidationError('A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?).', code='sem_caractere_especial')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('A senha deve conter pelo menos uma letra maiúscula.', code='sem_maiuscula')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('A senha deve conter pelo menos uma letra minúscula.', code='sem_minuscula')
    
    if not re.search(r'[0-9]', password):
        raise ValidationError('A senha deve conter pelo menos um número.', code='sem_numero')
    
    password_validators = get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
    validate_password(password, password_validators=password_validators)


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
        
        # Verifica se os campos obrigatórios não estão vazios
        if not self.username:
            messages.error(self.request, 'O nome de usuário é obrigatório.', extra_tags='usuario_vazio')
            is_valid = False
            return is_valid
            
        if not self.email:
            messages.error(self.request, 'O email é obrigatório.', extra_tags='email_vazio')
            is_valid = False
            return is_valid
            
        if not self.password1:
            messages.error(self.request, 'A senha é obrigatória.', extra_tags='senha_vazia')
            is_valid = False
            return is_valid
            
        if not self.password2:
            messages.error(self.request, 'A confirmação de senha é obrigatória.', extra_tags='senha2_vazia')
            is_valid = False
            return is_valid
        
        # Verifica se as senhas são iguais
        if self.password1 != self.password2:
            messages.error(self.request, 'As senhas não coincidem', extra_tags='senhas_diferentes')
            is_valid = False
            return is_valid

        # Verifica se o nome de usuário tem pelo menos 3 caracteres
        if len(self.username) < 3:
            messages.error(self.request, 'O nome de usuário deve ter pelo menos 3 caracteres.', extra_tags='usuario_curto')
            is_valid = False
            return is_valid

        # Verifica se o email tem formato válido
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            messages.error(self.request, 'Por favor, insira um email válido.', extra_tags='email_invalido')
            is_valid = False
            return is_valid

        return is_valid

    def validate_password(self):
        try:
            validate_password_strength(self.password1)
            return True
        except ValidationError as e:
            for message in e.messages:
                messages.error(self.request, message)
            return False

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
        
        return user # Confirma a transação e salva o usuário no banco de dados

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

# função para deletar usuários não verificados depois de 7 dias
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

def get_follow_counts(user):
    if not user.is_authenticated:
        return {'seguindo': 0, 'seguidores': 0}

    # 'seguindo' is the number of users `user` is following
    seguindo = Follow.objects.filter(seguidor=user).count()
    # 'seguidores' is the number of followers of `user`
    seguidores = Follow.objects.filter(seguindo=user).count()
    return {
        'seguindo': seguindo,
        'seguidores': seguidores
    }
    
def user_stats_processor(request):
    if not request.user.is_authenticated:
        return {'logged_in_user_stats': None}
    
    try:
        # Buscamos o usuário logado UMA VEZ com suas contagens anotadas
        # Usamos nomes longos e únicos para NUNCA colidir com as views
        user_with_stats = CustomUser.objects.annotate(
            processor_following_count = Count('seguidor', distinct=True),
            processor_followers_count = Count('seguindo', distinct=True),
        ).get(pk=request.user.pk)
        
        # Criamos um dicionário limpo para o template
        status_data = {
            'following_count': user_with_stats.processor_following_count,
            'followers_count': user_with_stats.processor_followers_count,
            'username': user_with_stats.username,
        }
        
        return {'logged_in_user_stats': status_data}
        
    except CustomUser.DoesNotExist:
        return {'logged_in_user_stats': None}


    
@receiver(post_delete, sender=CustomUser)
def deleta_imagem_ao_deletar_usuario(sender, instance, **kwargs):
    """
    Se o usuário for deletado do banco, deleta a foto dele do Cloudinary também.
    """
    if instance.avatar and hasattr(instance.avatar, 'public_id'):
        cloudinary.uploader.destroy(instance.avatar.public_id)

    if instance.capa and hasattr(instance.capa, 'public_id'):
        cloudinary.uploader.destroy(instance.capa.public_id)