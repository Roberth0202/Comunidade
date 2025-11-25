from .models import CustomUser
from django.db.models import Count

def follow_counts(request):
    """
    Um processador de contexto para adicionar as contagens de 'seguindo' e 'seguidores'
    do usuário logado a todos os contextos de template, usando uma única consulta.
    """
    if request.user.is_authenticated:
        user_with_counts = CustomUser.objects.annotate(
            following=Count('seguidor', distinct=True),  # Quantos o usuário logado segue
            followers=Count('seguindo', distinct=True)   # Quantos seguidores o usuário logado tem
        ).get(pk=request.user.pk)
        
        return {
            'logged_user_following_count': user_with_counts.following,
            'logged_user_followers_count': user_with_counts.followers,
        }
    return {}
