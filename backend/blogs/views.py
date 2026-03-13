"""
Blog API views.

Module này define ViewSet cho Blog API với:
- Optimization (select_related)
- Filtering, searching, ordering
- Pagination
- Action-based permissions
- Custom actions
"""
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from datetime import datetime

from .models import Blog
from .serializers import (
    BlogListSerializer,
    BlogDetailSerializer,
    BlogCreateUpdateSerializer,
)
from .permissions import IsAuthorOrReadOnly


class BlogPagination(PageNumberPagination):
    """
    Custom pagination cho Blog API.
    
    Default: 10 items per page
    Client có thể request tối đa 100 items per page
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BlogViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho Blog CRUD operations.
    
    Endpoints:
    - GET /api/blogs/                   - List all blogs (published only for unauthenticated)
    - POST /api/blogs/                  - Create new blog (authenticated only)
    - GET /api/blogs/{id}/              - Get blog detail
    - PUT /api/blogs/{id}/              - Update blog (author only)
    - PATCH /api/blogs/{id}/            - Partial update (author only)
    - DELETE /api/blogs/{id}/           - Delete blog (author only)
    - POST /api/blogs/{id}/publish/     - Publish blog (author only)
    - POST /api/blogs/{id}/unpublish/   - Unpublish blog (author only)
    - GET /api/blogs/my_blogs/          - Get current user's blogs (authenticated only)
    
    Filtering:
    - ?category=TECH                    - Filter by category
    - ?is_draft=false                   - Filter by draft status
    - ?search=keyword                   - Search in title and content
    - ?ordering=-created_at             - Order by field
    
    Pagination:
    - ?page=2                            - Get page 2
    - ?page_size=20                      - Get 20 items per page
    """
    
    # Optimize queryset với select_related để tránh N+1 queries
    queryset = Blog.objects.select_related('author').all()
    
    # Filtering, searching, ordering
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'published_date', 'title']
    ordering = ['-published_date', '-created_at']  # Default ordering
    
    # Pagination
    pagination_class = BlogPagination
    
    def get_serializer_class(self):
        """
        Return serializer class phù hợp với action.
        
        - list: BlogListSerializer (minimal fields)
        - retrieve: BlogDetailSerializer (full fields)
        - create/update: BlogCreateUpdateSerializer (write operations)
        """
        if self.action == 'list':
            return BlogListSerializer
        elif self.action == 'retrieve':
            return BlogDetailSerializer
        else:
            return BlogCreateUpdateSerializer
    
    def get_permissions(self):
        """
        Return permissions phù hợp với action.
        
        - list, retrieve: Public (anyone can view)
        - create: Authenticated users
        - update, partial_update, destroy: Author only
        - publish, unpublish, my_blogs: Authenticated users
        """
        if self.action in ['list', 'retrieve']:
            # Public endpoints - ai cũng xem được
            return [AllowAny()]
        elif self.action == 'create':
            # Create cần authenticated
            return [IsAuthenticated()]
        else:
            # Update, delete, custom actions cần author permission
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
    
    def get_queryset(self):
        """
        Customize queryset based on user, action, và query params.
        
        - Unauthenticated users: Chỉ xem published blogs
        - Authenticated users: Xem tất cả published blogs + own drafts
        - Authors: Xem tất cả own blogs (including drafts)
        
        Filtering query params hỗ trợ:
        - title: Search trong title (case-insensitive)
        - content: Search trong content (case-insensitive)
        - category: Filter by category (có thể multiple values)
        - is_draft: true/false
        - author: Author ID
        - author_username: Search trong author username
        - created_after: Blogs created sau ngày này (YYYY-MM-DD)
        - created_before: Blogs created trước ngày này (YYYY-MM-DD)
        - published_after: Blogs published sau ngày này (YYYY-MM-DD)
        - published_before: Blogs published trước ngày này (YYYY-MM-DD)
        """
        queryset = super().get_queryset()
        
        # Nếu không authenticated, chỉ hiện published blogs
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_draft=False, published_date__isnull=False)
        # Nếu authenticated nhưng action là list, hiện published + own drafts
        elif self.action == 'list':
            from django.db import models as django_models
            queryset = queryset.filter(
                django_models.Q(is_draft=False, published_date__isnull=False) |
                django_models.Q(author=self.request.user)
            ).distinct()
        
        # Apply custom filters từ query params
        params = self.request.query_params
        
        # Filter by title (case-insensitive contains)
        title = params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        # Filter by content (case-insensitive contains)
        content = params.get('content')
        if content:
            queryset = queryset.filter(content__icontains=content)
        
        # Filter by category (support multiple values)
        categories = params.getlist('category')
        if categories:
            queryset = queryset.filter(category__in=categories)
        
        # Filter by draft status
        is_draft = params.get('is_draft')
        if is_draft is not None:
            # Convert string to boolean
            is_draft_bool = is_draft.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_draft=is_draft_bool)
        
        # Filter by author ID
        author_id = params.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)
        
        # Filter by author username (case-insensitive contains)
        author_username = params.get('author_username')
        if author_username:
            queryset = queryset.filter(author__username__icontains=author_username)
        
        # Filter by created date range
        created_after = params.get('created_after')
        if created_after:
            try:
                date = datetime.fromisoformat(created_after)
                queryset = queryset.filter(created_at__gte=date)
            except (ValueError, TypeError):
                pass  # Ignore invalid date format
        
        created_before = params.get('created_before')
        if created_before:
            try:
                date = datetime.fromisoformat(created_before)
                queryset = queryset.filter(created_at__lte=date)
            except (ValueError, TypeError):
                pass
        
        # Filter by published date range
        published_after = params.get('published_after')
        if published_after:
            try:
                date = datetime.fromisoformat(published_after)
                queryset = queryset.filter(published_date__gte=date)
            except (ValueError, TypeError):
                pass
        
        published_before = params.get('published_before')
        if published_before:
            try:
                date = datetime.fromisoformat(published_before)
                queryset = queryset.filter(published_date__lte=date)
            except (ValueError, TypeError):
                pass
        
        return queryset

    def perform_create(self, serializer):
        """
        Set author khi create blog.
        
        Author được set tự động từ request.user.
        """
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """
        Validate author trước khi update.
        
        Chỉ author mới được update blog.
        """
        blog = self.get_object()
        if blog.author != self.request.user:
            raise PermissionDenied("Bạn không có quyền chỉnh sửa blog này")
        serializer.save()
        
    def destroy(self, request, *args, **kwargs):
        """
        Validate author trước khi delete.
        
        Chỉ author mới được delete blog.
        """
        blog = self.get_object()
        if blog.author != self.request.user:
            raise PermissionDenied("Bạn không có quyền xóa blog này")
        
        self.perform_destroy(blog)
        return Response(
            {"message": "Xóa blog thành công"},
            status=status.HTTP_204_NO_CONTENT
        )
    
    # Custom actions
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Custom action để publish blog.
        
        POST /api/blogs/{id}/publish/
        
        Set is_draft=False và published_date=now()
        """
        blog = self.get_object()
        
        # Check permission
        if blog.author != request.user:
            raise PermissionDenied("Bạn không có quyền publish blog này")
        
        # Validate có category chưa
        if not blog.category:
            return Response(
                {"error": "Blog phải có category trước khi publish"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publish blog
        blog.publish()
        
        serializer = BlogDetailSerializer(blog, context={'request': request})
        return Response(
            {
                "message": "Publish blog thành công",
                "blog": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """
        Custom action để unpublish blog (convert về draft).
        
        POST /api/blogs/{id}/unpublish/
        
        Set is_draft=True và published_date=null
        """
        blog = self.get_object()
        
        # Check permission
        if blog.author != request.user:
            raise PermissionDenied("Bạn không có quyền unpublish blog này")
        
        # Unpublish blog
        blog.unpublish()
        
        serializer = BlogDetailSerializer(blog, context={'request': request})
        return Response(
            {
                "message": "Unpublish blog thành công",
                "blog": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def my_blogs(self, request):
        """
        Custom action để lấy blogs của current user.
        
        GET /api/blogs/my_blogs/
        
        Return tất cả blogs (including drafts) của user hiện tại.
        """
        queryset = self.get_queryset().filter(author=request.user)
        
        # Apply filtering và searching
        queryset = self.filter_queryset(queryset)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BlogListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BlogListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def published(self, request):
        """
        Custom action để lấy tất cả published blogs.
        
        GET /api/blogs/published/
        
        Return tất cả blogs đã publish (public endpoint).
        """
        queryset = Blog.published.select_related('author').all()
        
        # Apply filtering và searching
        queryset = self.filter_queryset(queryset)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BlogListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BlogListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
