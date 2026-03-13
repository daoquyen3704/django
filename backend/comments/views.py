from django.shortcuts import render
from rest_framework import status, viewsets, permissions
from comments.models import Comment
from comments.serializers import CommmentSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticationOrReadOnly, AllowAny

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommmentSerializer
    permission_classes = [IsOwnerOrReadOnly, IsAuthenticationOrReadOnly]
    queryset = Comment.objects.selected_related('blog','author')
    
    # get_queryset → tối ưu DB + filter
    # get_serializer_class → đổi output theo action
    # perform_create → inject user
    # @action → custom endpoint

    def get_queryset(self): #Quyết định data trả về
        queryset =Comment.objects.select_related('author','blog')

        params = self.request.query_params
        # Filter theo blog
        blog_id = params.get('blog')
        # Nếu URL có id thì lọc tiếp theo id
        if blog_id:
            queryset = queryset.filter(blog_id=blog_id)
        
        return queryset.filter(is_active=True)
    
    
    


        


    
    

        






    
    

