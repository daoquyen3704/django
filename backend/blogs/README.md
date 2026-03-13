# Blog Module - Production Ready

Module Blog API được refactor hoàn toàn theo production best practices.

## 📁 Cấu trúc Files

```
blogs/
├── __init__.py
├── models.py          # Blog model với managers, properties, methods
├── serializers.py     # Multiple serializers cho different use cases
├── views.py          # ViewSet với filtering, pagination, custom actions
├── urls.py           # Router configuration
├── admin.py          # Enhanced Django admin
├── permissions.py    # Custom permissions
├── filters.py        # Custom filters với django-filter
├── managers.py       # Custom managers (Published, Draft)
└── tests.py          # Comprehensive tests
```

## ✨ Features

### 1. Model (`models.py`)

- ✅ Fixed duplicate category bug
- ✅ Corrected slug generation (exclude current instance khi update)
- ✅ Custom managers: `Blog.published`, `Blog.drafts`
- ✅ Properties: `is_published`, `reading_time`, `word_count`, `excerpt`
- ✅ Methods: `publish()`, `unpublish()`, `get_related_blogs()`
- ✅ Database indexes cho performance
- ✅ Full docstrings

### 2. Serializers (`serializers.py`)

- ✅ `BlogListSerializer` - Minimal fields cho list view
- ✅ `BlogDetailSerializer` - Full fields cho detail view
- ✅ `BlogCreateUpdateSerializer` - Cho write operations
- ✅ Custom validation cho title, content, featured_image
- ✅ Nested `AuthorSerializer`
- ✅ Explicit fields thay vì `__all__`

### 3. Views (`views.py`)

- ✅ Optimized queryset với `select_related('author')`
- ✅ Filtering by category, is_draft, author, dates
- ✅ Searching in title và content
- ✅ Pagination (10 items/page, max 100)
- ✅ Action-based permissions
- ✅ Custom actions: `publish`, `unpublish`, `my_blogs`, `published`
- ✅ Proper error handling

### 4. Admin (`admin.py`)

- ✅ Organized fieldsets
- ✅ Prepopulated slug
- ✅ Readonly fields
- ✅ Custom display columns với badges
- ✅ Bulk actions: publish/unpublish
- ✅ Date hierarchy navigation

### 5. Additional Files

- ✅ `permissions.py` - `IsAuthorOrReadOnly` permission
- ✅ `filters.py` - `BlogFilter` với date ranges, text search
- ✅ `managers.py` - `PublishedManager`, `DraftManager`

## 🚀 API Endpoints

### Standard CRUD

```
GET    /api/blogs/              # List all blogs (paginated)
POST   /api/blogs/              # Create new blog
GET    /api/blogs/{id}/         # Get blog detail
PUT    /api/blogs/{id}/         # Update blog
PATCH  /api/blogs/{id}/         # Partial update
DELETE /api/blogs/{id}/         # Delete blog
```

### Custom Actions

```
POST   /api/blogs/{id}/publish/     # Publish a draft
POST   /api/blogs/{id}/unpublish/   # Convert to draft
GET    /api/blogs/my_blogs/         # Get current user's blogs
GET    /api/blogs/published/        # Get all published blogs
```

### Query Parameters

**Filtering:**

```
?category=TECH              # Filter by category
?is_draft=false             # Filter published/draft
?author=1                   # Filter by author ID
?created_after=2024-01-01   # Created after date
?published_before=2024-12-31 # Published before date
```

**Searching:**

```
?search=django              # Search in title and content
```

**Ordering:**

```
?ordering=-created_at       # Order by created (newest first)
?ordering=title             # Order by title
```

**Pagination:**

```
?page=2                     # Get page 2
?page_size=20               # 20 items per page
```

## 📝 Usage Examples

### 1. Create Blog (Draft)

```python
POST /api/blogs/
Headers: Authorization: Bearer <token>

{
    "title": "My First Blog",
    "content": "This is the content...",
    "category": "TECH",
    "is_draft": true
}
```

### 2. Publish Blog

```python
POST /api/blogs/1/publish/
Headers: Authorization: Bearer <token>
```

### 3. Get My Blogs

```python
GET /api/blogs/my_blogs/
Headers: Authorization: Bearer <token>
```

### 4. Search Published Tech Blogs

```python
GET /api/blogs/published/?category=TECH&search=django
```

### 5. Get Latest Blogs with Pagination

```python
GET /api/blogs/?ordering=-published_date&page_size=20
```

## 🔒 Permissions

| Endpoint              | Permission          |
| --------------------- | ------------------- |
| `GET /blogs/`         | Public (anyone)     |
| `GET /blogs/{id}/`    | Public (anyone)     |
| `POST /blogs/`        | Authenticated users |
| `PUT /blogs/{id}/`    | Author only         |
| `DELETE /blogs/{id}/` | Author only         |
| Custom actions        | Author only         |

## 🎨 Custom Managers Usage

### Published Manager

```python
# Get all published blogs
Blog.published.all()

# Get recent published blogs
Blog.published.recent(limit=5)

# Get published blogs by category
Blog.published.by_category('TECH')
```

### Draft Manager

```python
# Get all drafts
Blog.drafts.all()

# Get drafts by author
Blog.drafts.by_author(user)
```

## 🔧 Model Methods

```python
blog = Blog.objects.get(id=1)

# Publish
blog.publish()  # Sets is_draft=False, published_date=now()

# Unpublish
blog.unpublish()  # Sets is_draft=True, published_date=None

# Get related blogs
related = blog.get_related_blogs(limit=3)

# Properties
blog.is_published      # True/False
blog.reading_time      # Minutes (int)
blog.word_count        # Word count (int)
blog.excerpt           # Short excerpt (str)
```

## 📊 Django Admin

Truy cập: `/admin/blogs/blog/`

Features:

- View list với status badges (Draft/Published)
- Quick edit category từ list view
- Search by title, content, author
- Filter by status, category, dates
- Bulk publish/unpublish actions
- Auto-generate slug from title
- Reading time display

## 🧪 Running Tests

```bash
python manage.py test blogs
```

## 🛠️ Installation & Setup

**1. Install dependencies:**

```bash
pip install djangorestframework django-filter Pillow
```

**2. Add to `INSTALLED_APPS`:**

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'django_filters',
    'blogs',
]
```

**3. Configure DRF settings:**

```python
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

**4. Run migrations:**

```bash
python manage.py makemigrations
python manage.py migrate
```

## 📚 What Changed?

### Models

- ❌ Category duplicate removed
- ✅ Slug logic fixed (exclude current instance)
- ✅ Added custom managers
- ✅ Added properties và methods
- ✅ Added database indexes

### Serializers

- ❌ Removed unsafe `fields='__all__'`
- ✅ Created separate serializers cho list/detail/create
- ✅ Added validation
- ✅ Added read_only_fields

### Views

- ❌ Removed all commented code
- ✅ Added select_related optimization
- ✅ Added filtering, searching, pagination
- ✅ Added action-based permissions
- ✅ Added custom actions

### Admin

- ✅ Added fieldsets
- ✅ Added bulk actions
- ✅ Added custom display methods
- ✅ Added filters và date hierarchy

## 🎯 Best Practices Applied

1. **DRY Principle**: Custom managers, reusable serializers
2. **Performance**: Database indexes, select_related, pagination
3. **Security**: Explicit permissions, validation
4. **Maintainability**: Full docstrings, organized code
5. **User Experience**: Good error messages, flexible API
6. **Production Ready**: Constraints, proper configuration

## 📞 Support

Nếu có vấn đề, check:

1. Migrations đã chạy chưa
2. Dependencies đã cài đủ chưa
3. Settings đã config DRF và django-filter chưa
4. User đã authenticated chưa (cho endpoints cần auth)
