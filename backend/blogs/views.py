from django.shortcuts import render
from rest_framework.response import Response
from blogs.models import Blog
from blogs.serializers import BlogSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404


#Create a Blog
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_blog(request):
    serializers = BlogSerializer(data=request.data)
    user = request.user
    if serializers.is_valid():
        serializers.save(author = user)
        return Response(serializers.data, status=status.HTTP_201_CREATED)
    return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)


#Get a blog
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_a_post(request, pk):
    blog = Blog.objects.get(id=pk)
    serializer = BlogSerializer(blog)
    return Response(serializer.data, status=status.HTTP_200_OK)


#Get all blogs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posts(request):
    blogs = Blog.objects.all()
    serializer = BlogSerializer(blogs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


#Update a blog
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_post(request, pk):
    user = request.user
    blog = Blog.objects.get(id=pk)
    if blog.author_id != user.id:
        return Response({"errors":"Bạn không phải là tác giả của Blog"}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = BlogSerializer(blog, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, pk):
    user = request.user
    blog = get_object_or_404(Blog, id=pk)
    if(blog.author_id != user.id):
        return Response({"errors":"Bạn không phải là tác giả của Blog"}, status=status.HTTP_403_FORBIDDEN)
    blog.delete()
    return Response({"status" : "Xóa Blog thành công"}, status = status.HTTP_204_NO_CONTENT)