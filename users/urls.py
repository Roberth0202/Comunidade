from django.urls import path
from . import views

urlpatterns = [
    # tela inicial da rede social
    path('/', views.index, name='home'),
    # tela de login
    path('/login/', views.login, name='login'),
    # tela de cadastro
    path('/cadastro/', views.cadastro, name='cadastro'),
    # tela de recuperação de senha
    path('/recuperar-senha/', views.recuperar_senha, name='recuperar_senha'),
    # tela de perfil
    path('/perfil/<usuario>', views.perfil, name='perfil'),
    # tela de configurações
    path('/configuracoes/', views.configuracoes, name='configuracoes'),
    # tela de ajuda
    path('/ajuda/', views.ajuda, name='ajuda'),
    # 
]
