from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Post, Comments
from .services import criar_post, criar_comentario
from users.services import get_follow_counts
import asyncio


# pagina feed para ver todos os posts
@login_required(login_url='login')
def feed_view(request):
    
    #cria um post do usuario logado
    if request.method == 'POST':
        #pega o conteudo do post
        content = request.POST.get('content')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        external_link = request.POST.get('link')
        
        if not content or content.strip() == '':
            messages.error(request, "O post não pode ser vazio!", extra_tags='alert-danger-post')
            return redirect('feed_view')
    
        #cria um novo post
        try:
            post = criar_post(
                author=request.user,
                content=content,
                image=image,
                video=video,
                external_link=external_link
            )
            messages.success(request, 'Post criado com sucesso!', extra_tags='alert-success-post')
            return redirect('feed_view')
        
        except Exception as e:
            messages.error(request, f'Erro ao criar o post', extra_tags='alert-danger-post')
            return redirect('feed_view')
    
    # busca todos os posts do banco de dados
    posts = Post.objects.select_related('author').order_by('-created_at').all()
    # converte o queryset para uma lista de dicionários
    posts = list(posts)
    
    follow_data = get_follow_counts(request.user)
    
    context = {
        'posts': posts,
        'seguindo': follow_data['seguindo'],
        'seguidores': follow_data['seguidores'],
    }
    
    return render(request, 'feed.html', context)

#pagina dos posts do usuario, que contem os comentarios e o post
@login_required(login_url='login')
def post_detail(request, username, post_id):
    # busca o post pelo id
    post = Post.objects.select_related('author').get(id=post_id)
    

    if request.method == 'POST':
        # pega o conteudo do comentario
        content = request.POST.get('content')
        comment_image = request.FILES.get('image')
        comment_video = request.FILES.get('video')
        comment_link = request.POST.get('link')
        
        
        # verifica se o comentario esta vazio
        if not content and not comment_image and not comment_video and not comment_link:
            messages.error(request, "Comentário vazio!", extra_tags='alert-danger-post')
            return redirect('post_detail', username=username, post_id=post_id)
        
        # cria um novo comentario
        criar_comentario(
            post=post,
            author=request.user,
            content=content,
            image=comment_image,
            video=comment_video,
            external_link=comment_link
        )
        
        # atualiza a contagem de comentarios do post
        post.comments_count += 1
        post.save()
        return redirect('post_detail', username=username, post_id=post_id)
    
    # busca os comentarios do post e converte os comentarios para uma lista de dicionários
    comments_list = list(post.comments.select_related('author').order_by('-created_at'))
    context = {
        'post': post,
        'comments': comments_list
    }
    
    return render(request, 'post_detail.html', context)