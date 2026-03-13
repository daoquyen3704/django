from urllib.request import Request
import uuid
from urllib.parse import urlparse
import os

from urllib3 import request
from storage.serializers import ImageAssetSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from botocore.exceptions import ClientError
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .models import ImageAsset
from .services.minio import get_s3_client


# Map extension → (ext, folder, mime_types)
ALLOWED_EXTENSIONS: dict[str, tuple[str, str, list[str]]] = {
    "zip": ("zip", "archives", ["application/zip", "application/x-zip-compressed", "application/octet-stream"]),
    "rar": ("rar", "archives", ["application/x-rar-compressed", "application/octet-stream"]),
    "7z":  ("7z",  "archives", ["application/x-7z-compressed", "application/octet-stream"]),
    "jpg": ("jpg", "images", ["image/jpeg"]),
    "jpeg": ("jpg", "images", ["image/jpeg"]),
    "png": ("png", "images", ["image/png"]),
    "gif": ("gif", "images", ["image/gif"]),
    "webp": ("webp", "images", ["image/webp"]),
    "svg": ("svg", "images", ["image/svg+xml"]),
    "mp4": ("mp4", "videos", ["video/mp4"]),
    "webm": ("webm", "videos", ["video/webm"]),
    "mov": ("mov", "videos", ["video/quicktime"]),
    "mp3": ("mp3", "audio", ["audio/mpeg"]),
    "wav": ("wav", "audio", ["audio/wav"]),
    "ogg": ("ogg", "audio", ["audio/ogg"]),
    "pdf": ("pdf", "docs", ["application/pdf"]),
    "txt": ("txt", "docs", ["text/plain"]),
    "csv": ("csv", "docs", ["text/csv"]),
    "json": ("json", "docs", ["application/json"]),
}

def validate_file_type(content_type: str, filename: str = None) -> tuple[str, str] | None:
    """
    Validate content_type, with fallback to filename extension.
    Returns (ext, folder) or None if invalid.
    """
    # Fallback: kiểm tra dựa vào extension
    if filename:
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext in ALLOWED_EXTENSIONS:
            ext_info, folder, allowed_mimes = ALLOWED_EXTENSIONS[ext]
            # Nếu content_type nằm trong danh sách cho extension này thì OK
            if content_type in allowed_mimes:
                return (ext_info, folder)
    
    return None

# Hàm này để làm gì? Để tạo URL có chữ ký (presigned URL) cho phép frontend upload hoặc download file 
# trực tiếp từ MinIO mà không cần qua backend. Backend sẽ tạo URL này dựa trên key và content_type, 
# sau đó frontend sẽ sử dụng URL này để tương tác với MinIO. Khi upload xong, 
# frontend sẽ gọi API confirm để backend kiểm tra file đã tồn tại và lấy size thực tế.
class PresignPutImageView(APIView):
    def post(self, request):
        #Lấy content_type
        content_type = request.data.get("content_type", "application/octet-stream")
        filename = request.data.get("filename", "")
        
        result = validate_file_type(content_type, filename)
        if not result:
            return Response(
                {
                    "detail": f"Loại file không hợp lệ. Content-Type: {content_type}",
                    "allowed_extensions": list(ALLOWED_EXTENSIONS.keys()),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        #xác định ext và folder dựa trên content_type hoặc extension
        ext, folder = result
        key = f"{folder}/{uuid.uuid4()}.{ext}"
        #Lưu DB với size=0, sẽ update sau khi confirm
        asset = ImageAsset.objects.create(key=key, content_type=content_type, size=0)

        client = get_s3_client()
        put_url = client.generate_presigned_url(
            'put_object',
            Params = {
                'Bucket' : settings.MINIO_BUCKET,
                'Key'    : key,
                'ContentType': content_type,
            },
            ExpiresIn = 3600,
        )
        return Response({
            "id": asset.id,
            "key": key,
            "put_url": put_url,
        }, status=status.HTTP_200_OK)

# API này để lấy presigned URL cho phép frontend tải file xuống trực tiếp từ MinIO. 
# Frontend sẽ gọi API này với id của asset, backend sẽ kiểm tra asset tồn tại, 
# sau đó tạo presigned URL cho phép download file. URL này sẽ có thời hạn (ExpiresIn) để đảm bảo an toàn. 
# Frontend sẽ sử dụng URL này để tải file về mà không cần qua backend, giúp giảm tải cho server.
class PresignGetImageView(APIView):
    def get(self, request, pk):
        content_type = request.query_params.get("content_type", "application/octet-stream")
        filename = request.query_params.get("filename", "")
        
        result = validate_file_type(content_type, filename)
        if not result:
            return Response(
                {
                    "detail": f"Loại file không hợp lệ. Content-Type: {content_type}",
                    "allowed_extensions": list(ALLOWED_EXTENSIONS.keys()),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        ext, folder = result
        key = f"{folder}/{uuid.uuid4()}.{ext}"
        
        ImageAsset.objects.create(key=key, content_type=content_type, size=0)
        client = get_s3_client()
        put_url = client.generate_presigned_url(
            'put_object',
            Params = {
                'Bucket' : settings.MINIO_BUCKET,
                'Key'    : key,
                'ContentType': content_type,
            },
            ExpiresIn = 3600,
        )
        return Response({
            "key": key,
            "put_url": put_url,
        }, status=status.HTTP_200_OK)


class ConfirmUploadedView(APIView):
    def post(self, request):
        key = request.data.get("key")
        asset_id = request.data.get("id")
        if not asset_id:
            return Response({"detail": "Thiếu asset_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            asset = ImageAsset.objects.get(pk=asset_id)
        except ImageAsset.DoesNotExist:
            return Response({"detail": "Asset không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_s3_client()

        try:
            head = client.head_object(
                Bucket=settings.MINIO_BUCKET,
                Key=asset.key,
            )
            size = int(head.get("ContentLength") or 0)
            if size == 0:
                return Response(
                    {"detail": "File upload chưa hoàn tất"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            asset.size = size
            asset.save(update_fields=["size"])
            return Response({"asset_id": asset_id, "key": asset.key, "size": size}, status=status.HTTP_200_OK)
        except ClientError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            

# MULTIPART UPLOAD
# Luồng:
#   1. POST /multipart/create/   → uploadId + key
#   2. POST /multipart/presign-part/ (x N lần) → presigned PUT URL cho từng part
#   3. Frontend PUT từng part thẳng lên MinIO → thu thập ETag
#   4. POST /multipart/complete/ → MinIO ghép các part lại

class MultipartCreateView(APIView):
    #POST body: { "content_type": "video/mp4", "filename": "myvideo.mp4" }
    #Response:  { "upload_id": "...", "key": "videos/<uuid>.mp4" }
    def post(self, request):
        content_type = request.data.get("content_type", "application/octet-stream")
        filename = request.data.get("filename", "")
        
        result = validate_file_type(content_type, filename)
        if not result:
            return Response(
                {
                    "detail": f"Loại file không hợp lệ. Content-Type: {content_type}",
                    "allowed_extensions": list(ALLOWED_EXTENSIONS.keys()),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext, folder = result
        key = f"{folder}/{uuid.uuid4()}.{ext}"

        client = get_s3_client()
        resp = client.create_multipart_upload(
            Bucket=settings.MINIO_BUCKET,
            Key=key,
            ContentType=content_type,
        )
        upload_id = resp["UploadId"] # ID do MinIO tạo ra để nhận diện multipart upload này. Frontend sẽ cần upload_id này để upload từng part và để complete sau này.

        # Lưu asset với size=0, sẽ update sau khi complete
        asset = ImageAsset.objects.create(key=key, content_type=content_type, size=0)
        # asset_id để làm gì? Để frontend có thể liên kết multipart upload với asset trong database. Khi complete multipart upload,
        # frontend sẽ gửi asset_id để backend biết update record nào với size thực tế sau khi upload xong.
        return Response(
            {"upload_id": upload_id, "key": key, "asset_id": asset.id},
            status=status.HTTP_200_OK,
        )


class MultipartPresignPartView(APIView):
    #POST body: { "key": "...", "upload_id": "...", "part_number": 1 }
    #Response:  { "url": "<presigned PUT URL>" }
    #Part number bắt đầu từ 1, tối đa 10000.
    def post(self, request):
        key = request.data.get("key")
        upload_id = request.data.get("upload_id")
        part_number = request.data.get("part_number")

        if not all([key, upload_id, part_number]):
            return Response({"detail": "Thiếu key, upload_id hoặc part_number"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            part_number = int(part_number)
            if not (1 <= part_number <= 10000):
                raise ValueError()
        except ValueError:
            return Response({"detail": "part_number phải là số từ 1 đến 10000"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_s3_client()
        url = client.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket":     settings.MINIO_BUCKET,
                "Key":        key,
                "UploadId":   upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=3600,
        )
        return Response({"url": url}, status=status.HTTP_200_OK)


class MultipartCompleteView(APIView):
    #POST body:
    #"asset_id": 1,
    #"key": "videos/<uuid>.mp4",
    #"upload_id": "...",
    #"parts": [
    #{ "part_number": 1, "etag": "\"abc123\"" },
    #{ "part_number": 2, "etag": "\"def456\"" }
    #]
    def post(self, request):
        asset_id  = request.data.get("asset_id")
        key       = request.data.get("key")
        upload_id = request.data.get("upload_id")
        parts     = request.data.get("parts", [])

        if not all([asset_id, key, upload_id, parts]):
            return Response({"detail": "Thiếu asset_id, key, upload_id hoặc parts"}, status=status.HTTP_400_BAD_REQUEST)

        multipart_parts = [
            {"PartNumber": p["part_number"], "ETag": p["etag"]}
            for p in parts
        ]

        client = get_s3_client()
        try:
            client.complete_multipart_upload(
                Bucket=settings.MINIO_BUCKET,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": multipart_parts},
            )
        except ClientError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Cập nhật size thực từ MinIO
        try:
            asset = ImageAsset.objects.get(pk=asset_id)
            head  = client.head_object(Bucket=settings.MINIO_BUCKET, Key=key)
            asset.size = int(head.get("ContentLength") or 0)
            asset.save(update_fields=["size"])
        except ImageAsset.DoesNotExist:
            pass

        return Response(
            {"asset_id": asset_id, "key": key, "status": "completed"},
            status=status.HTTP_200_OK,
        )


class MultipartAbortView(APIView):
    #POST body: { "key": "...", "upload_id": "..." }
    #Hủy multipart upload đang dở (giải phóng storage trên MinIO).
    def post(self, request):
        key       = request.data.get("key")
        upload_id = request.data.get("upload_id")
        if not all([key, upload_id]):
            return Response({"detail": "Thiếu key hoặc upload_id"}, status=status.HTTP_400_BAD_REQUEST)

        client = get_s3_client()
        try:
            client.abort_multipart_upload(
                Bucket=settings.MINIO_BUCKET,
                Key=key,
                UploadId=upload_id,
            )
        except ClientError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "aborted"}, status=status.HTTP_200_OK)




class ImageAssetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
class ListFileUploadsView(generics.ListAPIView):
    #trả ra danh sách file đã upload, có thể phân trang nếu cần
    queryset = ImageAsset.objects.all().order_by("-created_at")
    serializer_class = ImageAssetSerializer
    pagination_class = ImageAssetPagination

class DeleteFileUploadsView(generics.DestroyAPIView):
    queryset = ImageAsset.objects.all()
    serializer_class = ImageAssetSerializer
    look_up_field = "id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        client = get_s3_client()
        try:
            client.delete_object(Bucket=settings.MINIO_BUCKET, Key=instance.key)
        except ClientError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)