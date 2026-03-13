"""
Blog model với các best practices cho production.

Module này định nghĩa Blog model với đầy đủ:
- Slug generation logic đúng chuẩn
- Custom managers cho published/draft blogs
- Indexes để tối ưu performance
- Properties và methods hữu ích
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
import math

from .managers import PublishedManager, DraftManager


class Blog(models.Model):
    """
    Model đại diện cho một blog post.
    
    Attributes:
        title: Tiêu đề blog (bắt buộc)
        slug: URL-friendly slug (auto-generated từ title)
        content: Nội dung HTML của blog
        author: Tác giả (ForeignKey to User)
        created_at: Ngày tạo
        updated_at: Ngày cập nhật cuối
        published_date: Ngày publish (null nếu draft)
        is_draft: True nếu chưa publish
        category: Danh mục blog
        featured_image: Ảnh đại diện
    """
    
    # Constants cho categories - tách riêng để dễ maintain
    CATEGORY_TECH = 'TECH'
    CATEGORY_LIFESTYLE = 'LIFE'
    CATEGORY_TRAVEL = 'TRAVEL'
    CATEGORY_FOOD = 'FOOD'
    CATEGORY_SPORT = 'SPORT'
    CATEGORY_OTHER = 'OTHER'
    
    CATEGORY_CHOICES = [
        (CATEGORY_TECH, 'Technology'),
        (CATEGORY_LIFESTYLE, 'Lifestyle'),
        (CATEGORY_TRAVEL, 'Travel'),
        (CATEGORY_FOOD, 'Food'),
        (CATEGORY_SPORT, 'Sports'),
        (CATEGORY_OTHER, 'Other'),
    ]
    
    # Fields
    title = models.CharField(
        max_length=255,
        help_text="Tiêu đề blog post"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-friendly slug (tự động tạo từ title)"
    )
    content = models.TextField(
        help_text="Nội dung blog (hỗ trợ HTML)"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='blogs',
        null=True,
        blank=True,
        help_text="Tác giả của blog post"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Ngày publish blog (null nếu draft)"
    )
    is_draft = models.BooleanField(
        default=True,
        help_text="True nếu blog chưa publish"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
        help_text="Danh mục blog"
    )
    featured_image = models.ImageField(
        upload_to='blog_img/%Y/%m/',  # Organize by year/month
        blank=True,
        null=True,
        help_text="Ảnh đại diện cho blog"
    )
    
    # Managers - phải define objects trước để làm default
    objects = models.Manager()  # Default manager
    published = PublishedManager()  # Custom manager cho published blogs
    drafts = DraftManager()  # Custom manager cho draft blogs

    class Meta:
        db_table = "blog_posts"
        ordering = ['-published_date', '-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        
        # Indexes để tối ưu performance
        indexes = [
            models.Index(fields=['slug'], name='blog_slug_idx'),
            models.Index(fields=['category'], name='blog_category_idx'),
            models.Index(fields=['is_draft', 'published_date'], name='blog_published_idx'),
            models.Index(fields=['author', 'is_draft'], name='blog_author_draft_idx'),
            models.Index(fields=['-published_date'], name='blog_pub_date_desc_idx'),
        ]
        
        # Constraints : nó là luật đc nhét xuống DB
        constraints = [
            # Published blogs phải có published_date
            models.CheckConstraint(
                condition=models.Q(is_draft=True) | models.Q(is_draft=False, published_date__isnull=False),
                name='published_must_have_date'
            ),
        ]
        
    def __str__(self):
        """String representation của blog."""
        return self.title
    
    def save(self, *args, **kwargs):
        """
        Override save để auto-generate slug và set published_date.
        
        Logic:
        1. Generate slug từ title nếu chưa có
        2. Handle duplicate slugs bằng cách thêm số suffix
        3. Khi update, exclude current instance khỏi duplicate check
        4. Auto-set published_date khi publish lần đầu
        """
        # Generate slug nếu chưa có hoặc title thay đổi
        if not self.slug or self._state.adding:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            
            # Exclude current instance khi update
            qs = Blog.objects.filter(slug=slug)
            if self.pk:  # Nếu updating existing record
                qs = qs.exclude(pk=self.pk)
            
            # Find unique slug
            while qs.exists():
                slug = f"{base_slug}-{num}"
                num += 1
                qs = Blog.objects.filter(slug=slug)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                    
            self.slug = slug

        # Auto-set published_date khi publish lần đầu
        if not self.is_draft and not self.published_date:
            self.published_date = timezone.now()
        
        # Reset published_date nếu convert về draft
        if self.is_draft and self.published_date:
            self.published_date = None
            
        super().save(*args, **kwargs)
    
    # Properties - các computed fields hữu ích
    
    @property # Gọi các hàm như 1 field => blog.is_published
    def is_published(self): # có thể dùng serializer để lấy như 1 biến nạp vào API
        """
        Check xem blog đã published chưa.
        
        Returns:
            bool: True nếu blog đã published
        """
        return not self.is_draft and self.published_date is not None
    
    @property 
    def reading_time(self):
        """
        Tính thời gian đọc ước tính (giả sử 200 words/minute).
        
        Returns:
            int: Số phút đọc (tối thiểu 1 phút)
        """
        word_count = len(self.content.split())
        minutes = math.ceil(word_count / 200)
        return max(1, minutes)  # Tối thiểu 1 phút
    
    @property
    def word_count(self):
        """
        Đếm số từ trong content.
        
        Returns:
            int: Số từ
        """
        return len(self.content.split())
    
    @property
    def excerpt(self, length=200):
        """
        Lấy đoạn trích ngắn từ content.
        
        Args:
            length (int): Độ dài tối đa của excerpt
            
        Returns:
            str: Excerpt text
        """
        if len(self.content) <= length:
            return self.content
        return self.content[:length].rsplit(' ', 1)[0] + '...'
    
    # Methods
    
    def get_absolute_url(self):
        """
        Lấy URL canonical của blog.
        
        Returns:
            str: URL path của blog detail page
        """
        return reverse('blogs:blog-detail', kwargs={'pk': self.pk})
    
    def publish(self):
        """
        Publish blog (set is_draft=False và published_date).
        
        Returns:
            Blog: Self instance để có thể chain
        """
        self.is_draft = False
        if not self.published_date:
            self.published_date = timezone.now()
        self.save()
        return self
    
    def unpublish(self):
        """
        Convert blog về draft.
        
        Returns:
            Blog: Self instance để có thể chain
        """
        self.is_draft = True
        self.published_date = None
        self.save()
        return self
    
    def get_related_blogs(self, limit=5):
        """
        Lấy các blogs liên quan (cùng category, đã published).
        
        Args:
            limit (int): Số lượng blogs tối đa
            
        Returns:
            QuerySet: Danh sách related blogs
        """
        return Blog.published.filter(
            category=self.category
        ).exclude(
            pk=self.pk
        )[:limit]
