from django.urls import path
from . import views

urlpatterns = [
    # Feed de posts
    path('home/', views.feed_view, name='feed_view'),
    # Detalhes do post
    path('<str:username>/post/<int:post_id>/', views.post_detail, name='post_detail'),
]