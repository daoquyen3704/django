"""
Blog serializers cho API endpoints.

Module này define các serializers khác nhau cho từng use case:
- BlogListSerializer: Minimal fields cho list view (performance)
- BlogDetailSerializer: Full fields cho detail view
- BlogCreateUpdateSerializer: Cho create/update operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone


from .models import Blog


User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer cho Author information.
    
    Hiển thị thông tin cơ bản của tác giả trong blog.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields  # Tất cả fields đều read-only
    
    def get_full_name(self, obj):
        """Get full name của user."""
        return obj.get_full_name() or obj.username


class BlogListSerializer(serializers.ModelSerializer):
    """
    Serializer cho Blog list view.
    
    Chỉ include các fields cần thiết để tối ưu performance.
    Dùng cho endpoint GET /api/blogs/
    """
    author = AuthorSerializer(read_only=True)
    reading_time = serializers.IntegerField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    
    class Meta: # cấu hình các trường trong API Input/Output
        model = Blog
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'category',
            'featured_image',
            'is_draft',
            'is_published',
            'published_date',
            'created_at',
            'reading_time',
        ]
        read_only_fields = [
            'id',
            'slug',
            'created_at',
            'is_published',
            'reading_time',
        ]


class BlogDetailSerializer(serializers.ModelSerializer):
    """
    Serializer cho Blog detail view.
    
    Include tất cả fields và computed properties.
    Dùng cho endpoint GET /api/blogs/{id}/
    """
    author = AuthorSerializer(read_only=True)
    reading_time = serializers.IntegerField(read_only=True)
    word_count = serializers.IntegerField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    related_blogs = serializers.SerializerMethodField()
    
    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'author',
            'category',
            'featured_image',
            'is_draft',
            'is_published',
            'published_date',
            'created_at',
            'updated_at',
            'reading_time',
            'word_count',
            'related_blogs',
        ]
        read_only_fields = [
            'id',
            'slug',
            'created_at',
            'updated_at',
            'published_date',
            'is_published',
            'reading_time',
            'word_count',
        ]
    
    def get_related_blogs(self, obj):
        """
        Get related blogs (same category).
        
        Returns minimal info để avoid nested queries quá sâu.
        """
        related = obj.get_related_blogs(limit=3)
        return [{
            'id': blog.id,
            'title': blog.title,
            'slug': blog.slug,
            'category': blog.category,
        } for blog in related]


class BlogCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer cho Blog create và update operations.
    
    Dùng cho:
    - POST /api/blogs/
    - PUT /api/blogs/{id}/
    - PATCH /api/blogs/{id}/
    """
    
    class Meta:
        model = Blog
        fields = [
            'title',
            'content',
            'category',
            'featured_image',
            'is_draft',
        ]
    
    def validate_title(self, value):
        """
        Validate title không được trống và có độ dài hợp lý.
        
        Args:
            value: Title string
            
        Returns:
            str: Validated title
            
        Raises:
            ValidationError: Nếu title không hợp lệ
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Title không được để trống")
        
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title phải có ít nhất 5 ký tự")
        
        return value.strip()
    
    def validate_content(self, value):
        """
        Validate content không được trống.
        
        Args:
            value: Content string
            
        Returns:
            str: Validated content
            
        Raises:
            ValidationError: Nếu content không hợp lệ
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Content không được để trống")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content phải có ít nhất 10 ký tự")
        
        return value
    
    def validate_featured_image(self, value):
        """
        Validate featured image size và format.
        
        Args:
            value: Uploaded file
            
        Returns:
            File: Validated file
            
        Raises:
            ValidationError: Nếu file không hợp lệ
        """
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "File size quá lớn. Maximum 5MB."
                )
            
            # Check file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = value.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"File format không hợp lệ. Chỉ chấp nhận: {', '.join(allowed_extensions)}"
                )
        
        return value
    
    def validate(self, data):
        """
        Object-level validation.
        
        Validate logic giữa các fields với nhau.
        
        Args:
            data: Dict of all fields
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: Nếu data không hợp lệ
        """
        # Nếu publish (is_draft=False), phải có category
        if not data.get('is_draft', True) and not data.get('category'):
            raise serializers.ValidationError({
                'category': 'Category là bắt buộc khi publish blog'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Create blog instance.
        
        Author được set tự động từ request.user trong view.
        """
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update blog instance.
        
        Không cho phép thay đổi author.
        """
        # Remove author nếu có trong validated_data
        validated_data.pop('author', None)
        
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        """
        Customize output representation.
        
        Sau khi create/update, return full detail thay vì chỉ input fields.
        """
        # Use BlogDetailSerializer để return full data
        return BlogDetailSerializer(instance, context=self.context).data
