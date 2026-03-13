from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    # permission ở mức toàn view => chạy trước khi lấy objects
    def has_permission(self, request , view):
        if request.method in permissions.SAFE_METHODS:
            return True
        #SAFE_METHODS là gì? là request không làm thay đổi dữ liệu
        #GET -> cho qua
        #POST/PUT/PATCH/DELETE -> phải login
        return request.user and request.user.is_authenticated

    # permission ở mức object cụ thể
    # GET object → ai cũng xem được
    # PUT/PATCH/DELETE → chỉ author mới được
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user