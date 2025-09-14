from django.urls import path
from . import views

urlpatterns = [
    # tela de login
    path('login/', views.login, name='login'),
    # tela de cadastro
    path('cadastro/', views.cadastro, name='register'),
    # verificação de email
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    # tela de perfil
    path('perfil/<str:username>', views.profile, name='perfil'),
    # tela de editar perfil
    path('perfil/<int:id>/editar/', views.edit_profile, name='edit_profile'),
    # tela de configurações
    #path('configuracoes/', views.configuracoes, name='configuracoes'),
]
