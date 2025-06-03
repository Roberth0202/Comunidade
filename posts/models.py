from django.db import models
from django.conf import settings

# Cria o modelo de post
class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    # link, imagem e video externo
    external_link = models.models.URLField(blank=True, max_length=200)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True, verbose_name='Imagem do Post')
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True, verbose_name='Vídeo do Post')
    
    # enjamento do post
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f'{self.user.username} - {self.created_at.strftime("%d/%m/%Y")}'
    
    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
