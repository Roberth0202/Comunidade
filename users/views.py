from django.conf import Settings, settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import IntegrityError
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from .services import RegisterUser
from asgiref.sync import sync_to_async
from .forms import SolicitacaoRedefinicaoSenhaForm

# ------------------------------------------- PAGINA DE LOGIN ----------------------------------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        # Verifica se o usuário existe e se a senha está correta
        if user is not None:
            auth_login(request, user)
            return redirect('home') # Redireciona para a página inicial após o login bem-sucedido
        
        # Se o usuário não for encontrado ou a senha estiver incorreta
        else:
            messages.add_message(request, messages.ERROR, 'Email ou Senha incorretos', extra_tags='erro_login')
            return render(request, 'login.html')
        
    # Se o método for GET, renderiza a página de login
    return render(request, 'login.html')

# --------------------------------------- PAGINA DE CADASTRO ---------------------------------------
def cadastro(request):
    if request.method == 'POST':
        # Obtém os dados do formulário de cadastro
        validador = RegisterUser(
            request,
            username = request.POST.get('username', '').strip(),
            email = request.POST.get('email', '').strip(),
            password1 = request.POST.get('password1', '').strip(),
            password2 = request.POST.get('password2', '').strip(), 
            data_nascimento = request.POST.get('data_nascimento')
            )
        
        # Verifica se os dados do usuário são válidos (sincronamente)
        if not validador.is_valid():
            messages.error(request, 'Dados de cadastro inválidos. Verifique os campos e tente novamente.')
            return render(request, 'register.html')
        
        # valida a senha de acordo com as regras definidas
        if not validador.valid_password():
            return render(request, 'register.html')
        
        # se tudo estiver correto, tenta criar o usuário e captura conflitos de unicidade
        try:
            validador.create_user()
        
        except IntegrityError:
            messages.error(request, 'Usuário ou email já existe.')
            return render(request, 'register.html')
        
        return redirect('login')
        
    
    # Se o método for GET, renderiza a página de cadastro
    return render(request, 'register.html')

# ------------------------------------------- FUNÇÃO DE LOGOUT ----------------------------------------
@login_required
def logout_view(request):
    # se o usuário está autenticado deve sair da conta
    logout(request)
    return render(request, 'users/login.html')

# --------------------------------------------- PAGINA DE PERFIL ----------------------------------------
@login_required(login_url='login')
def profile(request, username):
    # Obtém o perfil do usuário pelo nome de usuário
    # Se o usuário não for encontrado, retorna um erro 404
    user = get_object_or_404(CustomUser, username=username)
    
    # verifica se o usuário autenticado é o mesmo do perfil
    is_owner = request.user == user
    
    context = {
        'perfil': user,
        'user': user,
        'is_owner': is_owner,
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
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil', username=user.username)
        
        # Se for GET, renderiza o formulário de edição
        return render(request, 'users/edit_profile.html', {'user': user})
    
    else:
        # Se o usuário não tiver permissão, redireciona para a página de perfil
        messages.error(request, 'Você não tem permissão para editar este perfil.')
        return redirect('perfil', username=user.username)

# ----------------------------------------------- verificaçao de email  ----------------------------------------
def verify_email(request, token):
        # Tenta obter o token de verificação do banco de dados
        token_obj = get_object_or_404(EmailVerificationToken, token=token)
        
        if token_obj.is_used:
            return redirect('login')
        
        if token_obj.is_expired:
            return redirect('login')

        
        # Marca o email do usuário como verificado e ativa a conta
        user = token_obj.user
        user.is_active = True # Ativa a conta do usuário
        user.e_verificado = True # Marca o email como verificado
        user.save() # Salva as alterações no usuário
        
        # Marca o token como usado
        token_obj.is_used = True
        token_obj.save()  # Salva as alterações no token

        # Realiza o login do usuário automaticamente
        auth_login(request, user)
        return redirect('home')  # Redireciona para a página inicial ou outra página desejada
    
#-------------------------------------------- REDEFINIR SENHA ----------------------------------------
# criar a pagina drecionamento para pagina que recebe o email
def password_reset(request):
    if request.method == 'POST':
        form = SolicitacaoRedefinicaoSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                user = CustomUser.objects.get(email=email)
                
                token = PasswordResetToken.objects.create(user=user)
                
                password_reset_url = f'{settings.SITE_URL}/password-reset/{token.token}/'
                
                # por enquanto imprimir no console pra ver se está funcionando
                print(f"link de redefinição de senha do {user.email}: {password_reset_url}")
                
                # logica de envio de email aqui
                
                
                messages.success(request,'Se um usuário com este email existir, um link de redefinição foi enviado.', extra_tags='email_reset_passoword')
                return redirect('password_reset')
                
            except CustomUser.DoesNotExist:
                messages.success(request,'Se um usuário com este email existir, um link de redefinição foi enviado.', extra_tags='email_reset_password')
                return redirect('password_reset')
    else:
        form = SolicitacaoRedefinicaoSenhaForm()
        
    return render(request, 'password_reset.html', {'form': form})
        

# criar pagina para colocar a senha nova
        