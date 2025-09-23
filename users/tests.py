from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, EmailVerificationToken
from django.utils import timezone
from datetime import timedelta
import uuid

class RegisterUserTest(TestCase):
    def setUp(self):
        # Configuração inicial para os testes
        self.client = Client()
        self.register_url = reverse('register') #reverse: simula a URL de cadastro
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
            'data_nascimento': '2000-01-01'
        } # simula os dados de registro válidos

    def test_register_page_GET(self):
        """Testa se a página de cadastro é carregada corretamente"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_user_POST_valid_data(self):
        """Testa o cadastro com dados válidos"""
        response = self.client.post(self.register_url, self.valid_user_data) # adiciona os dados de registro    
        self.assertEqual(response.status_code, 302)  # Redirecionamento após cadastro
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.first().username, 'testuser')
        self.assertEqual(CustomUser.objects.first().email, 'test@example.com')
        self.assertFalse(CustomUser.objects.first().is_active)  # Usuário inativo até verificar email
        self.assertFalse(CustomUser.objects.first().e_verificado)  # Email não verificado

    def test_register_user_POST_invalid_password_match(self):
        """Testa o cadastro com senhas diferentes"""
        data = self.valid_user_data.copy()
        data['password2'] = 'DifferentPassword123'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Permanece na página de cadastro
        self.assertEqual(CustomUser.objects.count(), 0)  # Nenhum usuário criado

    def test_register_user_POST_existing_username(self):
        """Testa o cadastro com nome de usuário já existente"""
        # Cria um usuário primeiro
        CustomUser.objects.create_user(
            username='testuser',
            email='another@example.com',
            password='TestPassword123',
            data_nascimento='2000-01-01'
        )
        
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, 200)  # Permanece na página de cadastro
        self.assertEqual(CustomUser.objects.count(), 1)  # Nenhum usuário adicional criado

    def test_register_user_POST_existing_email(self):
        """Testa o cadastro com email já existente"""
        # Cria um usuário primeiro
        CustomUser.objects.create_user(
            username='anotheruser',
            email='test@example.com',
            password='TestPassword123',
            data_nascimento='2000-01-01'
        )
        
        data = self.valid_user_data.copy()
        data['username'] = 'newuser' # adiciona um nome de usuário diferente
        response = self.client.post(self.register_url, data) #
        self.assertEqual(response.status_code, 200)  # Permanece na página de cadastro
        self.assertEqual(CustomUser.objects.count(), 1)  # Nenhum usuário adicional criado

class EmailVerificationTest(TestCase):
    def setUp(self):
        # Configuração inicial para os testes
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123',
            data_nascimento='2000-01-01',
            is_active=False,
            e_verificado=False
        )
        self.token = EmailVerificationToken.objects.create(user=self.user) # cria um token de verificação para o usuário
        self.verify_url = reverse('verify_email', args=[self.token.token]) # cria a URL de verificação com o token

    def test_verify_email_valid_token(self):
        """Testa a verificação de email com token válido"""
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, 302)  # Redirecionamento após verificação
        
        # Atualiza o usuário do banco de dados
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)  # Usuário ativado
        
        self.assertTrue(self.user.e_verificado)  # Email verificado
        
        # Verifica se o token foi marcado como usado
        self.token.refresh_from_db()
        self.assertTrue(self.token.is_used)

    def test_verify_email_used_token(self):
        """Testa a verificação de email com token já usado"""
        # Marca o token como usado
        self.token.is_used = True
        self.token.save()
        
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
        
        # Verifica se o usuário permanece inativo
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.e_verificado)

    def test_verify_email_expired_token(self):
        """Testa a verificação de email com token expirado"""
        # Define o token como expirado
        self.token.expires_at = timezone.now() - timedelta(hours=1)
        self.token.save()
        
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
        
        # Verifica se o usuário permanece inativo
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.e_verificado)

    def test_verify_email_invalid_token(self):
        """Testa a verificação de email com token inválido"""
        invalid_token = uuid.uuid4()
        invalid_url = reverse('verify_email', args=[invalid_token])
        
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)  # Página não encontrada
