from django.db import models

class ImageAsset(models.Model):
    key = models.CharField(max_length=255, unique=True)
    content_type = models.CharField(max_length=100, default="application/octet-stream")
    size = models.BigIntegerField(default=0)  # bytes (có thể update sau)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.key
