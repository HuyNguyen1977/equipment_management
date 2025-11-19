"""
Permissions cho REST API
"""
from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Chỉ staff mới có quyền write, user thường chỉ đọc
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_staff


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Chỉ owner hoặc staff mới có quyền truy cập
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # Kiểm tra nếu user là owner của object
        if hasattr(obj, 'requester'):
            return obj.requester == request.user
        if hasattr(obj, 'current_user'):
            return obj.current_user == request.user
        return False



