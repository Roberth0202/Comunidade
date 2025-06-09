from django.urls import path
from . import views

urlpatterns = [
    # Feed de posts
    path('/', views.feed_view, name='feed_view'),
    # Detalhes do post
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail_view'),
]