from rest_framework import serializers
from .models import Blog
from django.contrib.auth import get_user_model

class SimpleAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()  
        fields = ["id", "username", "first_name", "last_name"]


class BlogSerializer(serializers.ModelSerializer):
    author = SimpleAuthorSerializer(read_only=True)
    class Meta:
        model = Blog
        fields = '__all__' # bao gồm tất cả các trường của model Blog
    

