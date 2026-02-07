from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_blog, name='create_blog'),
    path('post/<int:pk>/',views.get_a_post, name='get_a_blog'),
    path('posts/', views.get_posts, name='get_blogs'),
    path('update/<int:pk>/', views.update_post, name='update_blogs'),
    path('delete/<int:pk>/', views.delete_post, name="delete_blog")
]