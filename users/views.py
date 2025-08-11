from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout
from  django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from .services import RegisterUser
from asgiref.sync import sync_to_async

# ------------------------------------------- PAGINA DE LOGIN ----------------------------------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        # Verifica se o usuário existe e se a senha está correta
        if user is not None:
            login(request, user)
            return redirect('home') # Redireciona para a página inicial após o login bem-sucedido
        
        # Se o usuário não for encontrado ou a senha estiver incorreta
        else:
            messages.add_message(request, messages.ERROR, 'Email ou Senha incorretos', extra_tags='erro_login')
            return render(request, 'login.html')
        
    # Se o método for GET, renderiza a página de login
    return render(request, 'login.html')

# --------------------------------------- PAGINA DE CADASTRO ---------------------------------------
async def cadastro(request):
    if request.method == 'POST':
        # Obtém os dados do formulário de cadastro
        validador = RegisterUser(
            request,
            username = request.POST.get('username'),
            email1 = request.POST.get('email1'),
            email2 = request.POST.get('email2'),
            password1 = request.POST.get('password1'),
            password2 = request.POST.get('password2'), 
            data_nascimento = request.POST.get('data_nascimento')
            )
        
        # Verifica se os dados do usuário são válidos
        validacao = await sync_to_async(validador.is_valid)()
        # Se a validação falhar, retorna o render do template com a mensagem de erro
        if validacao is not True:
            return validacao # retorna o render do template com a mensagem de erro
        
        # valida a senha de acordo com as regras definidas
        validacao = await sync_to_async(validador.valid_password)()
        # Se a validação da senha falhar, retorna o render do template com a mensagem de erro
        if validacao is not True:
            return validacao
        
        # se tudo estiver correto, cria o usuário
        return await sync_to_async(validador.create_user)()
        
    
    # Se o método for GET, renderiza a página de cadastro
    return render(request, 'register.html')

# ------------------------------------------- FUNÇÃO DE LOGOUT ----------------------------------------
@login_required
def logout_view(request):
    # se o usuário está autenticado deve sair da conta
    logout(request)
    return render(request, 'users/login.html')

# --------------------------------------------- PAGINA DE PERFIL ----------------------------------------
@login_required
def profile(request, username):
    # Obtém o perfil do usuário pelo nome de usuário
    # Se o usuário não for encontrado, retorna um erro 404
    user = get_object_or_404(CustomUser, username=username)
    # Verifica se o usuário autenticado é o mesmo do perfil
    profile = user
    
    # verifica se o usuário autenticado é o mesmo do perfil
    perfil_proprio = request.user.is_authenticated and request.user == user
    
    context = {
        'perfil': profile,
        'user': user,
        'perfil_proprio': perfil_proprio,
    }
    return render(request, 'users/profile.html', context)

# ----------------------------------------------- PAGINA DE EDITAR PERFIL ----------------------------------------
@login_required
def edit_profile(request, id):
    user = request.user # Obtém o id do usuário autenticado
    
    # Verifica se o usuário tem permissão para editar o perfil
    if user.id == id:
        if request.method == 'POST':
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.avatar = request.FILES.get('avatar', user.avatar)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.data_nascimento = request.POST.get('data_nascimento', user.data_nascimento)
            user.save()
            return render(request, 'users/profile.html', {'user': user, 'success': 'Perfil atualizado com sucesso'})    
    else:
        # Se o usuário não tiver permissão, redireciona para a página de perfil
        messages.error(request, 'Você não tem permissão para editar este perfil.')
        return redirect('perfil', usuario=user.username)
        # nota: criar condição no template para verificar se o usuário é o mesmo do perfil
    return render(request, 'users/edit_profile.html', {'user': user})

# ----------------------------------------------- PAGINA DE TROCA DE SENHA ----------------------------------------
