"""
Tests cho Blog module.

Test coverage:
- Model methods và properties
- API endpoints
- Permissions
- Filters
- Serializers
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Blog


User = get_user_model()


class BlogModelTest(TestCase):
    """Test Blog model methods và properties."""
    
    def setUp(self):
        """Setup test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.blog = Blog.objects.create(
            title='Test Blog',
            content='This is a test blog content with multiple words to test reading time calculation.',
            author=self.user,
            category=Blog.CATEGORY_TECH,
            is_draft=True
        )
    
    def test_slug_generation(self):
        """Test slug được tạo tự động từ title."""
        self.assertEqual(self.blog.slug, 'test-blog')
    
    def test_slug_uniqueness(self):
        """Test slug unique khi có duplicate title."""
        blog2 = Blog.objects.create(
            title='Test Blog',
            content='Another blog',
            author=self.user
        )
        self.assertEqual(blog2.slug, 'test-blog-1')
    
    def test_is_published_property(self):
        """Test is_published property."""
        # Draft blog
        self.assertFalse(self.blog.is_published)
        
        # Publish blog
        self.blog.publish()
        self.assertTrue(self.blog.is_published)
    
    def test_reading_time(self):
        """Test reading time calculation."""
        self.assertGreaterEqual(self.blog.reading_time, 1)
    
    def test_word_count(self):
        """Test word count."""
        word_count = len(self.blog.content.split())
        self.assertEqual(self.blog.word_count, word_count)
    
    def test_publish_method(self):
        """Test publish method."""
        self.assertTrue(self.blog.is_draft)
        self.assertIsNone(self.blog.published_date)
        
        self.blog.publish()
        self.blog.refresh_from_db()
        
        self.assertFalse(self.blog.is_draft)
        self.assertIsNotNone(self.blog.published_date)
    
    def test_unpublish_method(self):
        """Test unpublish method."""
        self.blog.publish()
        self.assertFalse(self.blog.is_draft)
        
        self.blog.unpublish()
        self.blog.refresh_from_db()
        
        self.assertTrue(self.blog.is_draft)
        self.assertIsNone(self.blog.published_date)
    
    def test_published_manager(self):
        """Test PublishedManager."""
        # Create some blogs
        Blog.objects.create(
            title='Published Blog',
            content='Content',
            author=self.user,
            is_draft=False,
            published_date=timezone.now()
        )
        
        # Draft blog không nằm trong published
        published_count = Blog.published.count()
        self.assertEqual(published_count, 1)
        
        # Total blogs = 2 (1 draft + 1 published)
        total_count = Blog.objects.count()
        self.assertEqual(total_count, 2)
    
    def test_draft_manager(self):
        """Test DraftManager."""
        # self.blog là draft
        draft_count = Blog.drafts.count()
        self.assertEqual(draft_count, 1)


class BlogAPITest(APITestCase):
    """Test Blog API endpoints."""
    
    def setUp(self):
        """Setup test data."""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Create blogs
        self.blog1 = Blog.objects.create(
            title='Blog 1',
            content='Content 1',
            author=self.user1,
            category=Blog.CATEGORY_TECH,
            is_draft=False,
            published_date=timezone.now()
        )
        
        self.draft_blog = Blog.objects.create(
            title='Draft Blog',
            content='Draft content',
            author=self.user1,
            is_draft=True
        )
    
    def test_list_blogs_unauthenticated(self):
        """Test list blogs without authentication."""
        response = self.client.get('/api/blogs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Chỉ published blogs visible
        self.assertEqual(response.data['count'], 1)
    
    def test_list_blogs_authenticated(self):
        """Test list blogs với authentication."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/blogs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Published + own drafts
        self.assertEqual(response.data['count'], 2)
    
    def test_create_blog_unauthenticated(self):
        """Test create blog without authentication."""
        data = {
            'title': 'New Blog',
            'content': 'New content',
            'category': Blog.CATEGORY_TECH,
        }
        
        response = self.client.post('/api/blogs/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_blog_authenticated(self):
        """Test create blog với authentication."""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'title': 'New Blog',
            'content': 'New content here',
            'category': Blog.CATEGORY_TECH,
            'is_draft': True
        }
        
        response = self.client.post('/api/blogs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check author được set tự động
        blog = Blog.objects.get(id=response.data['id'])
        self.assertEqual(blog.author, self.user1)
    
    def test_update_blog_by_author(self):
        """Test update blog by author."""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'category': Blog.CATEGORY_LIFESTYLE
        }
        
        response = self.client.patch(
            f'/api/blogs/{self.blog1.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.title, 'Updated Title')
    
    def test_update_blog_by_non_author(self):
        """Test update blog by non-author (should fail)."""
        self.client.force_authenticate(user=self.user2)
        
        data = {
            'title': 'Hacked Title'
        }
        
        response = self.client.patch(
            f'/api/blogs/{self.blog1.id}/',
            data,
            format='json'
        )
        
        # Nên bị từ chối
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_blog_by_author(self):
        """Test delete blog by author."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.delete(f'/api/blogs/{self.draft_blog.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Blog.objects.filter(id=self.draft_blog.id).exists())
    
    def test_publish_action(self):
        """Test publish custom action."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(f'/api/blogs/{self.draft_blog.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft_blog.refresh_from_db()
        self.assertFalse(self.draft_blog.is_draft)
        self.assertIsNotNone(self.draft_blog.published_date)
    
    def test_my_blogs_action(self):
        """Test my_blogs custom action."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/blogs/my_blogs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # user1 có 2 blogs
        self.assertEqual(response.data['count'], 2)
    
    def test_filtering_by_category(self):
        """Test filtering by category."""
        # Create blog with different category
        Blog.objects.create(
            title='Food Blog',
            content='Food content',
            author=self.user1,
            category=Blog.CATEGORY_FOOD,
            is_draft=False,
            published_date=timezone.now()
        )
        
        response = self.client.get('/api/blogs/?category=TECH')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Chỉ TECH blogs
        self.assertEqual(response.data['count'], 1)
    
    def test_searching(self):
        """Test search functionality."""
        response = self.client.get('/api/blogs/?search=Blog 1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tìm được blog1
        results = response.data['results']
        self.assertTrue(any(blog['id'] == self.blog1.id for blog in results))


class BlogSerializerTest(TestCase):
    """Test Blog serializers."""
    
    def setUp(self):
        """Setup test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_validation_title_too_short(self):
        """Test validation cho title quá ngắn."""
        from .serializers import BlogCreateUpdateSerializer
        
        data = {
            'title': 'Hi',  # Quá ngắn
            'content': 'Some content here',
        }
        
        serializer = BlogCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_validation_content_too_short(self):
        """Test validation cho content quá ngắn."""
        from .serializers import BlogCreateUpdateSerializer
        
        data = {
            'title': 'Valid Title',
            'content': 'Short',  # Quá ngắn
        }
        
        serializer = BlogCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
    
    def test_validation_publish_without_category(self):
        """Test validation khi publish mà không có category."""
        from .serializers import BlogCreateUpdateSerializer
        
        data = {
            'title': 'Valid Title',
            'content': 'Valid content here',
            'is_draft': False,  # Publish
            # category missing
        }
        
        serializer = BlogCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)


# Run tests:
# python manage.py test blogs
