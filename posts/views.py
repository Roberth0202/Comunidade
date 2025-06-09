from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Post, comments
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
    
    # busca os comentarios do post
    comments_list = await sync_to_async(post.comments.select_related('author').order_by('-created_at').all)()
    
    # converte os comentarios para uma lista de dicionários
    comments_list = await sync_to_async(list)(comments_list)
    
    context = {
        'post': post,
        'comments': comments_list
    }
    
    return render(request, 'posts/post_detail.html', context)