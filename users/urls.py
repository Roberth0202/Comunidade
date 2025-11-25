from django.urls import path
from . import views

urlpatterns = [
    # tela de login
    path('login/', views.login, name='login'),
    # tela de logout
    path('logout/', views.logout_view, name='logout'),
    # tela de cadastro
    path('cadastro/', views.cadastro, name='register'),
    # verificação de email
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    # tela de perfil
    path('perfil/<str:username>/', views.profile, name='perfil'),
    # tela de editar perfil
    path('editar/', views.edit_profile, name='edit_profile'),
    # seguir usuario
    path('follow/<int:user_id>/', views.seguir_usuario, name='seguir_usuario'),
    # deixa de seguir
    path('unfollow/<int:user_id>/', views.deixar_de_seguir, name='deixar_de_seguir'),
    # recuperação de senha
    path('password-reset/', views.password_reset, name='password_reset'),
    # confirmação de recuperação de senha
    path('password-reset-confirm/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    # tela de configurações
    #path('configuracoes/', views.configuracoes, name='configuracoes'),
]
