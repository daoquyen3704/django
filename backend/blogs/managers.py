"""
Custom managers for Blog model.

Managers giúp encapsulate các query logic phổ biến,
giúp code DRY và dễ maintain hơn.
"""
from django.db import models
from django.utils import timezone


class PublishedManager(models.Manager):
    """
    Custom manager để query các blogs đã published.
    
    Usage:
        Blog.published.all()  # Lấy tất cả blogs đã publish
        Blog.published.filter(category='TECH')  # Lấy tech blogs đã publish
    """
    
    def get_queryset(self):
        """
        Override queryset mặc định để chỉ lấy blogs đã published.
        
        Returns:
            QuerySet: Chỉ các blogs có is_draft=False và published_date not null
        """
        return super().get_queryset().filter(
            is_draft=False,
            published_date__isnull=False
        )
    
    def recent(self, limit=5):
        """
        Lấy các blogs published gần đây nhất.
        
        Args:
            limit (int): Số lượng blogs cần lấy
            
        Returns:
            QuerySet: Danh sách blogs mới nhất
        """
        return self.get_queryset().order_by('-published_date')[:limit]
    
    def by_category(self, category):
        """
        Lấy các blogs published theo category.
        
        Args:
            category (str): Category code (VD: 'TECH', 'LIFE')
            
        Returns:
            QuerySet: Danh sách blogs trong category
        """
        return self.get_queryset().filter(category=category)


class DraftManager(models.Manager):
    """
    Custom manager để query các blogs draft.
    
    Usage:
        Blog.drafts.all()  # Lấy tất cả drafts
    """
    
    def get_queryset(self):
        """
        Override queryset mặc định để chỉ lấy blogs draft.
        
        Returns:
            QuerySet: Chỉ các blogs có is_draft=True
        """
        return super().get_queryset().filter(is_draft=True)
    
    def by_author(self, author):
        """
        Lấy drafts của một tác giả cụ thể.
        
        Args:
            author: User object hoặc user ID
            
        Returns:
            QuerySet: Danh sách drafts của author
        """
        return self.get_queryset().filter(author=author)
