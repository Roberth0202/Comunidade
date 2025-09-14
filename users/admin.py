from django.contrib import admin
from .models import CustomUser, EmailVerificationToken, Follow
# 

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'data_nascimento', 'e_verificado', 'bio', 'is_staff', 'is_active','data_criacao')
    list_filter = ('is_staff', 'is_active', 'e_verificado')
    search_fields = ('username', 'email')