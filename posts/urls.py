from django.urls import path
from . import views

urlpatterns = [
    # Feed de posts
    path('', views.feed_view, name='home'),
    # Detalhes do post
    path('<str:username>/post/<int:post_id>/', views.post_detail, name='post_detail'),
]