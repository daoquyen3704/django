"""
Custom permissions cho Blog API.

Permissions này control việc ai có thể read/write blogs.
"""
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission: chỉ author của blog mới có thể edit/delete.
    
    - GET, HEAD, OPTIONS: Public (anyone can read)
    - POST: Authenticated users có thể tạo blog
    - PUT, PATCH, DELETE: Chỉ author của blog mới được phép
    
    Usage trong ViewSet:
        permission_classes = [IsAuthorOrReadOnly]
    """
    
    def has_permission(self, request, view):
        """
        Check permission ở view level (trước khi get object).
        
        Args:
            request: HTTP request object
            view: View being accessed
            
        Returns:
            bool: True nếu có permission
        """
        # Read permissions cho tất cả mọi người
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions chỉ cho authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check permission ở object level (sau khi get object).
        
        Args:
            request: HTTP request object
            view: View being accessed
            obj: Blog object being accessed
            
        Returns:
            bool: True nếu có permission
        """
        # Read permissions cho tất cả mọi người
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions chỉ cho author của blog
        # obj ở đây là Blog instance
        return obj.author == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission: Chỉ owner hoặc admin mới edit được.
    
    Strict hơn IsAuthorOrReadOnly một chút, vì admin cũng có quyền.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin."""
        # Admin có full permission
        if request.user and request.user.is_staff:
            return True
        
        # Read permissions cho tất cả
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions chỉ cho owner
        return obj.author == request.user
