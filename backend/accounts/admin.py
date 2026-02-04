from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
# Register your models here.
class CustomUserAdmin(UserAdmin):
    #danh sách các cột hiển thị trong admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'bio', 'facebook', 'youtube', 'instagram', 'profile_picture')

admin.site.register(CustomUser, CustomUserAdmin)