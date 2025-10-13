from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.contrib import messages
from .services import RegisterUser
from .forms import SolicitacaoRedefinicaoSenhaForm, RedefinicaoSenhaForm
from django.utils import timezone
from datetime import timedelta

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
            messages.error(request, 'Email ou Senha incorretos')
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
        
        # Verifica se os dados do usuário são válidos (formato, etc.)
        if not validador.is_valid():
            return render(request, 'register.html')
        
        # valida a senha de acordo com as regras definidas
        if not validador.validate_password():
            return render(request, 'register.html')
        
        # Agora, lida com a lógica de existência de usuário/email
        try:
            # 1. Verifica se o nome de usuário já existe
            if CustomUser.objects.filter(username=validador.username).exists():
                messages.error(request, 'Este nome de usuário já está em uso. Por favor, escolha outro.')
                return render(request, 'register.html')

            # 2. Verifica se o email já existe
            if CustomUser.objects.filter(email=validador.email).exists():
                # Não revela que o e-mail já existe. redireciona pra pagina login.
                # Opcionalmente, você pode enviar um e-mail para o endereço existente aqui.
                messages.success(request, 'Se uma conta com este e-mail existir, um link de verificação será enviado em breve.')
                return redirect('login')

            # 3. Se tudo estiver ok, cria o usuário e envia o email de verificação
            user = validador.create_user()
            validador.send_email_verification(user)
            messages.success(request, 'Cadastro realizado com sucesso! Um e-mail de verificação foi enviado para o seu endereço.')
            return redirect('login')
        
        except IntegrityError:
            # Fallback para o caso de uma race condition (dois cadastros ao mesmo tempo)
            messages.error(request, 'Este nome de usuário ou e-mail já está em uso. Por favor, tente outro.')
            return render(request, 'register.html', context)
        
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
                password_reset_url = f'{settings.SITE_URL}/password-reset-confirm/{token.token}/'
                
                html_content= render_to_string('email/password_reset_email.html',{
                    'user':user,
                    'password_reset_url':password_reset_url,
                    'SITE_NAME':settings.SITE_NAME,
                    'SITE_URL': settings.SITE_URL,
                })
                
                text_content = strip_tags(html_content)
                
                send_mail(
                    subject="Redefinição de senha",
                    message = text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_content,
                )
                
                return render(request, 'password_reset.html', {'success': True})
                
            except CustomUser.DoesNotExist:
                return render(request, 'password_reset.html', {'success': True})
        # If form is NOT valid, we fall through to the final render call
    else:
        # This is a GET request, so create a blank form
        form = SolicitacaoRedefinicaoSenhaForm()
    
    # This single return handles both GET requests and POST requests with invalid forms
    return render(request, 'password_reset.html', {'form': form})

# criar pagina para colocar a senha nova
def password_reset_confirm(request, token):
    try:
        token_obj = get_object_or_404(PasswordResetToken, token=token)
        user = token_obj.user
        
        if token_obj.created_at < timezone.now() - timedelta(hours=1):
            messages.error(request, 'Token expirado. Por favor, solicite uma nova redefinição de senha.')
            token_obj.delete() # Remove o token expirado
            return redirect('password_reset')
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Token inválido ou expirado.')
        return redirect('password_reset')
    
    if request.method == "POST":
        form = RedefinicaoSenhaForm(request.POST)
        if form.is_valid():
            nova_senha = form.cleaned_data['nova_senha']
            
            # Atualiza a senha do usuário
            user.set_password(nova_senha)
            user.save()
            
            # Remove o token após a redefinição bem-sucedida
            token_obj.delete()
            
            messages.success(request, 'Sua senha foi redefinida com sucesso!')
            return redirect('login')
    
    else:
        form = RedefinicaoSenhaForm()
    
    return render(request, 'password_reset_confirm.html', {'form': form})