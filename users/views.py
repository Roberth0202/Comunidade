from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from .models import CustomUser, EmailVerificationToken, PasswordResetToken, Follow
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.contrib import messages
from .services import RegisterUser
from .forms import EditUserForm, SolicitacaoRedefinicaoSenhaForm, RedefinicaoSenhaForm
from django.views.decorators.http import require_POST
from django.db.models import Count, Exists, OuterRef

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

def logout_view(request):
    logout(request)
    return redirect('login')

# --------------------------------------- PAGINA DE CADASTRO ---------------------------------------
def cadastro(request):
    if request.method == 'POST':
        # Obtém os dados do formulário de cadastro
        validador = RegisterUser(
            request,
            username = request.POST.get('username', '').strip(),
            email = request.POST.get('email', '').strip().lower(),
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
            return render(request, 'register.html')
        
    # Se o método for GET, renderiza a página de cadastro
    return render(request, 'register.html')

# ------------------------------------------- SISTEMA DE SEGUIDOR ----------------------------------------
@login_required(login_url='login')
@require_POST
def seguir_usuario(request, user_id):
    user_to_follow = get_object_or_404(CustomUser, pk=user_id)
    
    usuario_logado = request.user
    
    if usuario_logado == user_to_follow:
        return redirect('perfil', user_id=user_to_follow.pk)
    
    Follow.objects.get_or_create(
        seguidor=usuario_logado,
        seguindo=user_to_follow
    )
    
    return redirect('perfil', username=user_to_follow.username)

@login_required(login_url='login')
@require_POST
def deixar_de_seguir(request, user_id):
    user_to_unfollow = get_object_or_404(CustomUser, pk=user_id)
    
    usuario_logado = request.user
    
    if usuario_logado == user_to_unfollow:
        return redirect('perfil', user_id=user_to_unfollow.pk)
    
    relacionamento = Follow.objects.filter(
        seguidor=usuario_logado,
        seguindo=user_to_unfollow
    )
    
    if relacionamento.exists():
        relacionamento.delete()
    
    return redirect('perfil', username=user_to_unfollow.username)

# --------------------------------------------- PAGINA DE PERFIL ----------------------------------------
@login_required(login_url='login')
def profile(request, username):
    user_logado = request.user

    # --- Otimização 1: Subquery com Exists ---
    # Preparamos uma subquery para checar se o user_logado
    # segue o usuário do perfil (OuterRef se refere à query principal)
    is_following_subquery = Follow.objects.filter(
        seguidor = user_logado,
        seguindo = OuterRef('pk') # 'pk/primery key' é do CustomUser da query principal
    )  # retorna True se o user_logado segue o usuário do perfil, False caso contrário
    
    # --- A GRANDE QUERY OTIMIZADA ---
    # Buscamos o usuário pelo username, ao mesmo tempo, anotamos (adicionamos) 
    # as contagens e o status de "seguir" nele.
    perfil_user = get_object_or_404(
        CustomUser.objects.annotate(
            # Contagem de quantos ELES seguem
            following_count = Count('seguidor', distinct=True),
            # Contagem de quantos OS seguem
            follows_count = Count('seguindo', distinct=True),
            # Booleano: o user_logado segue este perfil?
            is_following = Exists(is_following_subquery)
        ),
        username=username
    )
    
    is_owner = user_logado == perfil_user
    
    # As contagens já vieram na query (não precisamos de get_follow_counts)
    profile_follow_data = {
        'seguindo': perfil_user.following_count,
        'seguidores': perfil_user.follows_count,
    }

    is_following = perfil_user.is_following

    context = {
        'perfil_user': perfil_user,
        'is_owner': is_owner,
        # Contadores para a página de perfil (do perfil_user)
        'num_seguindo': profile_follow_data['seguindo'],
        'num_seguidores': profile_follow_data['seguidores'],
        'is_following': is_following,
    }
    return render(request, 'profile.html', context)

# ----------------------------------------------- PAGINA DE EDITAR PERFIL ----------------------------------------
@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = EditUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil', username=user.username)
    else:
        form = EditUserForm(instance=user)
    
    context = {
        'form': form,
    }
    return render(request, 'edit_user.html', context)

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
        messages.success(request, 'Email verificado com sucesso!')
        return redirect('login')  # Redireciona para a página inicial ou outra página desejada
    
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
                if settings.DEBUG:
                    messages.error(request, f"O e-mail {email} não foi encontrado em nosso sistema.")
                return render(request, 'password_reset.html', {'success': True})
        # If form is NOT valid, we fall through to the final render call
    else:
        # This is a GET request, so create a blank form
        form = SolicitacaoRedefinicaoSenhaForm()
    
    # This single return handles both GET requests and POST requests with invalid forms
    return render(request, 'password_reset.html', {'form': form})

def password_reset_confirm(request, token):
    try:
        token_obj = get_object_or_404(PasswordResetToken, token=token)
        user = token_obj.user
        
        if token_obj.is_expired:
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