from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
# Create your models here.
class Blog(models.Model):
    CATEGORY = [
        ('TECH', 'Technology'),
        ('LIFE', 'Lifestyle'),   
        ('TRAVEL', 'Travel'),
        ('FOOD', 'Food'),
        ('SPORT', 'Sports'),
        ('LIFE', 'Lifestyle'),
        ('OTHER', 'Other'),
    ]
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='blogs', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(blank=True, null=True)
    is_draft = models.BooleanField(default=True)
    category = models.CharField(max_length=50, choices=CATEGORY, blank=True, null=True)
    featured_image = models.ImageField(upload_to='blog_img/', blank=True, null=True)

    class Meta:
        db_table = "blog_posts"
        ordering = ['-published_date']
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        base_slug = slugify(self.title)
        slug = base_slug
        num = 1
        while Blog.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{num}"
            num += 1
        self.slug = slug


        if not self.published_date and not self.is_draft:
            self.published_date = timezone.now()
        # nhận toàn bộ tham số và gọi hàm save của lớp cha
        super().save(*args, **kwargs)
