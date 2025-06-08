from django.contrib.auth.models import AbstractUser
from django.db import models

# Usuario personalizado para a rede social
class CustomUser(AbstractUser):
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
        
class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Seguir'
        verbose_name_plural = 'Seguir'
        
