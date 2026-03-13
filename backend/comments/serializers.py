from rest_framework import serializers
from .models import Comments
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','username']
        read_only_field = fields
    

class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = Comments
        fields = ['id', 'blog', 'author', 'content', 'parent', 'is_active']
        read_only_fields = ['author']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content không được để trống")
        
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Content phải có ít nhất 5 ký tự")
        
        return value.strip()

class CommentDetailSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = Comments
        fields = ["id", "blog", "author", "content", "parent", "replies", "created_at"]
        read_only_fields = ["author"]

    def get_replies(self, obj):
        queryset = obj.replies.filter(is_active=True).select_related("author")
        return CommentSerializer(queryset,many=True).data



    
