"""
URL configuration cho Blog app.

Sử dụng DefaultRouter để auto-generate standard REST endpoints.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BlogViewSet


app_name = 'blogs'

# Setup router
router = DefaultRouter(trailing_slash=True)
router.register(r'blogs', BlogViewSet, basename='blog')

# URL patterns
# Router sẽ tự động generate các endpoints:
# - GET    /blogs/              -> list
# - POST   /blogs/              -> create
# - GET    /blogs/{id}/         -> retrieve
# - PUT    /blogs/{id}/         -> update
# - PATCH  /blogs/{id}/         -> partial_update
# - DELETE /blogs/{id}/         -> destroy
# - POST   /blogs/{id}/publish/ -> publish (custom action)
# - POST   /blogs/{id}/unpublish/ -> unpublish (custom action)
# - GET    /blogs/my_blogs/     -> my_blogs (custom action)
# - GET    /blogs/published/    -> published (custom action)
urlpatterns = router.urls

