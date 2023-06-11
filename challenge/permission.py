from rest_framework.permissions import BasePermission


class IsJudge(BasePermission):
    message = "You are not judge."

    def has_permission(self, request, view):
        return getattr(request, "is_judge", False)
