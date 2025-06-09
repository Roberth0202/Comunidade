from django.urls import path
from . import views

urlpatterns = [
    # tela inicial da rede social
    path('/', views.index, name='home'),
    # tela de login
    path('login/', views.login, name='login_view'),
    # tela de cadastro
    path('cadastro/', views.cadastro, name='register_view'),
    # tela de recuperação de senha
    path('recuperar-senha/', views.recuperar_senha, name='recuperar_senha'),
    # tela de perfil
    path('perfil/<str:usuario>', views.perfil, name='perfil'),
    # tela de editar perfil
    path('perfil/<int:id>/editar/', views.editar_perfil, name='edit_profile'),
    # tela de configurações
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    # tela de ajuda
    path('ajuda/', views.ajuda, name='ajuda'),
    # 
]
