from django.db import models
from django.conf import settings
from django.utils import timezone

from blogs.models import Blog

# Create your models here.
class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    #replies: vì là optiopnal nên có thể null 
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blog_comments"
        ordering = ['-created_at'] # thiết lập Order By khi query : created_at DESC (có - là DESC)
        verbose_name = "Blog Comment" # Tên trong admin
        verbose_name_plural = "Blog Comments" # Tên số nhiều, giúp chuẩn hóa tên trong admin

    
    def __str__(self):
        return f"{self.author}-{self.blog}"   
