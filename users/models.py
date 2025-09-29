from django.contrib.auth.models import AbstractUser
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models

# Usuario personalizado para a rede social
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    bio = models.TextField(max_length=280, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, verbose_name='Avatar')
    data_nascimento = models.DateField(null=False, blank=False, verbose_name='Data de Nascimento')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    e_verificado = models.BooleanField(default=False, verbose_name='Email Verificado')
    # No AbstractUser ja tem o campo (username, email, password,first_name,
    # last_name, date_joined, is_active, is_staff, is_superuser, last_login)
    
    def __str__(self):
        return f'{self.username} - {self.data_criacao.strftime("%d/%m/%Y")}'

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-data_criacao']


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # user: Relaciona o token com o usuário (ForeignKey: Chave estrangeira, on_delete=models.CASCADE: Se o usuário for deletado, deleta também os tokens relacionados)
    token = models.UUIDField(default=uuid.uuid4, unique=True) # UUID: Gera identificador único tipo a1b2c3d4-e5f6-7890-abcd-ef1234567890, default=uuid.uuid4: Gera automaticamente quando criar o token , unique=True: Garante que não existam tokens duplicados
    created_at = models.DateTimeField(auto_now_add=True) # created_at: Salva automaticamente quando o token é criado
    expires_at = models.DateTimeField() # expires_at: Definido manualmente (veremos no save())
    is_used = models.BooleanField(default=False) # is_used: Indica se o token já foi usado, e impedir que seja reutilizado
    
    # Define o tempo de expiração do token (24 horas)
    def save(self, *args, **kwargs): 
        if not self.expires_at:
            # Se o campo expires_at não estiver definido, define como 24 horas a partir do momento atual
            self.expires_at = timezone.now() + timedelta(hours=24) 
        super().save(*args, **kwargs) # Chama o método save() da classe pai para salvar o objeto no banco de dados
    
    # Propriedade para verificar se o token está expirado
    @property 
    def is_expired(self):
        return timezone.now() > self.expires_at # Retorna True se o token estiver expirado, caso contrário, retorna False
    
    class Meta:
        ordering = ['-created_at']
        
class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Seguir'
        verbose_name_plural = 'Seguir'

class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_user = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
        
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    class Meta:
        ordering = ['-created_at']