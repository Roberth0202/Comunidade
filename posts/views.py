from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Post, Comments
from.services import criar_post, criar_comentario
import asyncio


# pagina feed para ver todos os posts
@login_required
async def feed(request):
    
    #cria um post do usuario logado
    if request.method == 'POST':
        #pega o conteudo do post
        content = request.POST.get('content')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        external_link = request.POST.get('link')
        
        #cria um novo post
        try:
            post = await sync_to_async(criar_post)(
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
    posts = await sync_to_async(Post.objects.select_related('author').order_by('-created_at').all)()
    # converte o queryset para uma lista de dicionários
    posts = await sync_to_async(list)(posts)
    context = {
        'posts': posts
    }
    
    return render(request, 'posts/feed.html', context)

#pagina dos posts do usuario, que contem os comentarios e o post
@login_required
async def post_detail(request, post_id):
    # busca o post pelo id
    post = await sync_to_async(Post.objects.select_related('author').get)(id=post_id)
    

    if request.method == 'POST':
        # pega o conteudo do comentario
        content = request.POST.get('content')
        comment_image = request.FILES.get('image')
        comment_video = request.FILES.get('video')
        comment_link = request.POST.get('link')
        
        # verifica se o comentario esta vazio
        if not content and not comment_image and not comment_video and not comment_link:
            messages.error(request, "Comentário vazio!", extra_tags='alert-danger-post')
            return redirect('post_detail_view', post_id=post_id)
        
        # cria um novo comentario
        await sync_to_async(criar_comentario)(
            post=post,
            author=request.user,
            content=content,
            image=comment_image,
            video=comment_video,
            external_link=comment_link
        )
        
        # atualiza a contagem de comentarios do post
        post.comments_count += 1
        await sync_to_async(post.save)()
        return redirect('post_detail_view', post_id=post_id)
    
    # busca os comentarios do post e converte os comentarios para uma lista de dicionários
    comments_list = await sync_to_async(list)(post.comments.select_related('author').order_by('-created_at'))
    context = {
        'post': post,
        'comments': comments_list
    }
    
    return render(request, 'posts/post_detail.html', context)