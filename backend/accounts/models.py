from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.

class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    facebook = models.TextField(max_length=255, blank=True, null=True)
    youtube = models.TextField(max_length=255, blank=True, null=True)
    instagram = models.TextField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(blank=True, null=True, upload_to='profile_img/')

    def __str__(self):
        return self.username # biến thành tên hiển thị cho user


