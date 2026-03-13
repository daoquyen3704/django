from django.urls import path
from .views import (
    DeleteFileUploadsView, ListFileUploadsView, PresignPutImageView, PresignGetImageView, ConfirmUploadedView,
    MultipartCreateView, MultipartPresignPartView,
    MultipartCompleteView, MultipartAbortView,
)

urlpatterns = [
    path("presign-put/",          PresignPutImageView.as_view()),
    path("images/<int:pk>/url/",  PresignGetImageView.as_view()),
    path("confirm/",              ConfirmUploadedView.as_view()),

    # File lớn
    path("multipart/create/",       MultipartCreateView.as_view()),
    path("multipart/presign-part/", MultipartPresignPartView.as_view()),
    path("multipart/complete/",     MultipartCompleteView.as_view()),
    path("multipart/abort/",        MultipartAbortView.as_view()),

    #list file đã upload
    path("uploads/", ListFileUploadsView.as_view()),
    path("uploads/<int:pk>/", DeleteFileUploadsView.as_view()),
]
