from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import get_password_validators, validate_password
from django.contrib import messages
from comuna.settings import AUTH_PASSWORD_VALIDATORS

# ------------------------------------------- PAGINA DE LOGIN ----------------------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        # Verifica se o usuário existe e se a senha está correta
        if user is not None:
            login(request, user)
            return render(request, 'users/profile.html', {'user': user})
        # Se o usuário não for encontrado ou a senha estiver incorreta
        else:
            return render(request, 'users/login.html', {'error': 'Nome ou Senha incorretos'})
    # Se o método for GET, renderiza a página de login
    return render(request, 'users/login.html')

# --------------------------------------- PAGINA DE CADASTRO ---------------------------------------
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        
        
        # Verifica se as senhas são iguais
        if password1 != password2:
            messages.error(request, 'As senhas não coincidem', extra_tags='senhas_diferentes')
            return render(request, 'users/register.html')
        # Verifica se o usuário já existe        
        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': 'Usuário já existe'})
        # Verifica se o email já está cadastrado
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'users/register.html', {'error': 'Email já cadastrado'})
        
        validar_senha = get_password_validators(settings=AUTH_PASSWORD_VALIDATORS)
        # Valida a senha de acordo com as regras definidas
        try:
            validate_password(password1, user=None, password_validators=validar_senha)
        except Exception as e:
            return render(request, 'users/register.html', {'error': str(e)})

        # Cria um novo usuário
        user = CustomUser.objects.create_user(username=username, password=password1, email=email, data_nascimento=data_nascimento)
        user.save()
        
        return redirect('login/')  # Redireciona para a página de login após o cadastro bem-sucedido
    
    # Se o método for GET, renderiza a página de cadastro
    return render(request, 'users/register.html')

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
    perfil = get_object_or_404(CustomUser, username=username)
    # Verifica se o usuário autenticado é o mesmo do perfil
    user = request.user
    
    context = {
        'perfil': perfil,
        'user': user,
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
