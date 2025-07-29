from django.db import models
from django.conf import settings

# Cria o modelo de post
class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts') # Relaciona o post com o usuário que o criou
    content = models.TextField(max_length=280) # Conteúdo do post, limitado a 280 caracteres
    created_at = models.DateTimeField(auto_now_add=True) # Cria automaticamente quando o post é criado
    
    # link, imagem e video externo
    external_link = models.URLField(blank=True, max_length=200)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True, verbose_name='Imagem do Post')
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True, verbose_name='Vídeo do Post')
    
    # enjamento do post
    likes_count = models.IntegerField(default=0) # Contador de likes do post
    comments_count = models.IntegerField(default=0) # Contador de comentários do post
    shares_count = models.IntegerField(default=0) # Contador de compartilhamentos do post
    
    def __str__(self):
        return f'{self.user.username} - {self.created_at.strftime("%d/%m/%Y")}' 
    
    class Meta: 
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

# Criar o modelo para comentarios dos post
class Comments(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments') # Relaciona o comentário com o post ao qual ele pertence
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments') # Relaciona o comentário com o usuário que o criou
    content = models.TextField(max_length=280) # Conteúdo do comentário, limitado a 280 caracteres
    created_at = models.DateTimeField(auto_now_add=True) # Cria automaticamente quando o comentário é criado
    updated_at = models.DateTimeField(auto_now=True) # Atualiza automaticamente quando o comentário é editado

    # Comentários podem ser respondidos, então podemos ter um campo para o comentário pai
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Enjamento do comentário
    likes_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    # Link externo opcional, imagem e vídeo
    external_link = models.URLField(blank=True, null=True, max_length=200) # Link externo opcional
    image = models.ImageField(upload_to='media/images/', blank=True, null=True, verbose_name='Imagem do Comentário')
    video = models.FileField(upload_to='media/videos/', blank=True, null=True, verbose_name='Vídeo do Comentário')
    
    def __str__(self):
        return f'{self.author.username} - {self.created_at.strftime("%d/%m/%Y")}'
    
    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'