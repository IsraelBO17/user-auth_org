from rest_framework.permissions import IsAuthenticated


class IsMember(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.users.filter(userId=request.user.userId).exists()