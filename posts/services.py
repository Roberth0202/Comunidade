from .models import Post, Comments

def criar_post(author, content=None, image=None, video=None, external_link=None):
    """
    Função para criar um novo post.
    """
    if not content:
        raise ValueError("O conteúdo do post não pode ser vazio.")
    post = Post.objects.create(
        author=author,
        content=content if content else None,
        image=image if image else None,
        video=video if video else None,
        external_link=external_link if external_link else None
    )
    return post

def criar_comentario(post, author, content=None, image=None, video=None, external_link=None, parent_comment=None):
    """
    Função para criar um novo comentário em um post.
    """
    comentario = Comments.objects.create(
        post=post,
        author=author,
        content=content if content else None,
        image=image if image else None,
        video=video if video else None,
        external_link=external_link if external_link else None,
        parent_comment=parent_comment if parent_comment else None
    )
    return comentario