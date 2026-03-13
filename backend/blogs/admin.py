"""
Django Admin configuration cho Blog model.

Enhanced admin với:
- Organized fieldsets
- Bulk actions
- Advanced filters
- Search optimization
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """
    Admin interface cho Blog model.
    
    Features:
    - Fieldsets để organize form
    - Prepopulated slug từ title
    - Readonly fields
    - List display với custom columns
    - Filters và search
    - Bulk actions
    """
    
    # List view configuration
    list_display = (
        'title',
        'author_name',
        'category',
        'status_badge',
        'published_date',
        'created_at',
        'reading_time_display',
    )
    
    list_filter = (
        'is_draft',
        'category',
        'created_at',
        'published_date',
    )
    
    search_fields = (
        'title',
        'content',
        'author__username',
        'author__email',
    )
    
    list_editable = ('category',)  # Có thể edit category trực tiếp từ list view
    
    list_per_page = 20
    
    date_hierarchy = 'created_at'  # Navigate by date
    
    # Form configuration
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ('Nội dung', {
            'fields': ('content', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('is_draft', 'published_date'),
            'description': 'Quản lý trạng thái publish của blog'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Collapse by default
        }),
    )
    
    readonly_fields = (
        'slug',
        'created_at',
        'updated_at',
        'published_date',
    )
    
    prepopulated_fields = {'slug': ('title',)}  # Auto-generate slug từ title
    
    # Ordering
    ordering = ('-created_at',)
    
    # Autocomplete
    autocomplete_fields = ['author']
    
    # Custom methods cho list display
    
    @admin.display(description='Author', ordering='author__username')
    def author_name(self, obj):
        """Display author name với link."""
        if obj.author:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.author.id,
                obj.author.username
            )
        return '-'
    
    @admin.display(description='Status', ordering='is_draft')
    def status_badge(self, obj):
        """Display status với colored badge."""
        if obj.is_draft:
            return format_html(
                '<span style="background-color: #ffc107; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
                'Draft'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
                'Published'
            )
    
    @admin.display(description='Reading Time')
    def reading_time_display(self, obj):
        """Display reading time."""
        return f"{obj.reading_time} min"
    
    # Bulk actions
    
    @admin.action(description='Publish selected blogs')
    def make_published(self, request, queryset):
        """Bulk action để publish blogs."""
        updated = 0
        for blog in queryset:
            if blog.is_draft:
                blog.publish()
                updated += 1
        
        self.message_user(
            request,
            f"{updated} blog(s) đã được published successfully."
        )
    
    @admin.action(description='Unpublish selected blogs')
    def make_draft(self, request, queryset):
        """Bulk action để unpublish blogs."""
        updated = queryset.update(
            is_draft=True,
            published_date=None
        )
        
        self.message_user(
            request,
            f"{updated} blog(s) đã được converted về draft."
        )
    
    actions = ['make_published', 'make_draft']
    
    # Override save_model để auto-set author nếu chưa có
    
    def save_model(self, request, obj, form, change):
        """Auto-set author nếu creating new blog."""
        if not change and not obj.author:  # Creating new và chưa có author
            obj.author = request.user
        super().save_model(request, obj, form, change)


