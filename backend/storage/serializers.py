from rest_framework import serializers
from django.contrib.auth import get_user_model # lấy model user tùy chỉnh
from .models import ImageAsset

class ImageAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAsset
        fields = ('id', 'key', 'content_type', 'size', 'created_at')
        read_only_fields = ('id', 'key', 'content_type', 'size', 'created_at')
