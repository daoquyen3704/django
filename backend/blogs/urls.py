from django.urls import path
# from . import views
from .views import BlogViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blog')

# urlpatterns = [
#     path('create/', views.create_blog, name='create_blog'),
#     path('post/<int:pk>/',views.get_a_post, name='get_a_blog'),
#     path('posts/', views.get_posts, name='get_blogs'),
#     path('update/<int:pk>/', views.update_post, name='update_blogs'),
#     path('delete/<int:pk>/', views.delete_post, name="delete_blog")
# ]

urlpatterns = router.urls
