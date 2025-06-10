from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Post, Comments
import asyncio


# pagina feed para ver todos os posts
@login_required
async def feed_view(request):
    # busca todos os posts do banco de dados
    posts = Post.objects.select_related('author').order_by('-created_at')
    # converte o queryset para uma lista de dicionários
    posts = await sync_to_async(list)(posts)
    
    return render(request, 'posts/feed.html', {'posts': posts})

#pagina dos posts do usuario, que contem os comentarios e o post
@login_required
async def post_detail_view(request, post_id):
    # busca o post pelo id
    post = await sync_to_async(Post.objects.select_related('author').get)(id=post_id)
    
    if request.method == 'POST':
        # verifica se o usuario esta logado
        if not request.user.is_authenticated:
            return redirect('login_view')
        
        # pega o conteudo do comentario
        content = request.POST.get('content')
        
        # cria um novo comentario
        await sync_to_async(Comments.objects.create)(
            post=post,
            author=request.user,
            content=content
        )
        
        # atualiza a contagem de comentarios do post
        post = await sync_to_async(Post.objects.get)(id=post_id)
        post.comments_count += 1
        await sync_to_async(post.save)()
        
        return redirect('post_detail_view', post_id=post_id)
    
    # busca os comentarios do post
    comments_list = await sync_to_async(list)(post.comments.select_related('author').order_by('-created_at'))
    
    # converte os comentarios para uma lista de dicionários
    comments_list = await sync_to_async(list)(comments_list)
    
    context = {
        'post': post,
        'comments': comments_list
    }
    
    return render(request, 'posts/post_detail.html', context)