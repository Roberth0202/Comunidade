# Este arquivo contém testes automatizados para as views de posts e comentários do app 'posts'.
# Utiliza o framework de testes do Django para garantir que as funcionalidades principais estão funcionando corretamente.
# Os testes cobrem:
# - Carregamento da página de feed
# - Criação de posts (sucesso e falha)
# - Carregamento da página de detalhes do post
# - Criação de comentários (sucesso e falha)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Post, Comments
from datetime import date
from django.urls import reverse

User = get_user_model()

class FeedViewtest(TestCase):
    def setUp(self):
        # Cria um usuário para autenticação nos testes do feed
        self.user = User.objects.create_user(username='testuser', password='123456', data_nascimento=date(2000, 1, 1))
        self.client = Client()
        self.client.login(username='testuser', password='123456')

    def test_feed_view(self):
        # Testa se a página de feed carrega corretamente e utiliza o template esperado
        response = self.client.get(reverse('feed_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feed.html')

    def test_create_post(self):
        # Testa se um novo post é criado com sucesso e redireciona após a criação
        response = self.client.post(reverse('feed_view'), {
            'content': 'Video novo no canal Alanzoka',
            'link': 'https://www.youtube.com/@alanzoka'
        })
        self.assertEqual(response.status_code, 302)  # Redireciona para a página de feed após criar o post
        self.assertTrue(Post.objects.filter(content='Video novo no canal Alanzoka').exists())

    def test_create_post_failure(self):
        # Testa se a tentativa de criar um post com conteúdo vazio falha e não cria o post
        response = self.client.post(reverse('feed_view'), {
            'content': '',  # Conteúdo vazio
            'link': ''
        })
        self.assertEqual(response.status_code, 302)  # Redireciona para a página de feed após falhar ao criar o post
        self.assertFalse(Post.objects.filter(content='').exists())


class PostDetailViewTest(TestCase):
    def setUp(self):
        # Cria um usuário e um post para os testes de detalhes do post
        self.user = User.objects.create_user(username='testuser', password='123456', data_nascimento=date(2000, 1, 1))
        self.post = Post.objects.create(author=self.user, content='Post de teste')
        self.client = Client()
        self.client.login(username='testuser', password='123456')

    def test_post_detail_page_loads(self):
        # Testa se a página de detalhes do post carrega corretamente e utiliza o template esperado
        response = self.client.get(reverse('post_detail', args=[self.user.username, self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post_detail.html')

    def test_create_comment_success(self):
        # Testa se um comentário é criado com sucesso e redireciona após a criação
        response = self.client.post(reverse('post_detail', args=[self.post.author.username, self.post.id]), {
            'content': 'Comentário de teste'
        })
        self.assertEqual(response.status_code, 302)  # Redireciona após criar o comentário
        self.assertTrue(Comments.objects.filter(content='Comentário de teste').exists())

    def test_create_comment_failure(self):
        # Testa se a tentativa de criar um comentário com conteúdo vazio falha e não cria o comentário
        response = self.client.post(reverse('post_detail', args=[self.post.author.username, self.post.id]), {
            'content': ''
        })
        self.assertEqual(response.status_code, 302)  # Redireciona mesmo em caso de erro
        self.assertFalse(Comments.objects.filter(content='').exists())