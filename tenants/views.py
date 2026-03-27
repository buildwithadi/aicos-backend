from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .serializers import UserSerializer

class TenantAwareModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that automatically filters all database queries by request.user.school.
    All future Module ViewSets (StudentProfileViewSet, AttendanceViewSet, InvoiceViewSet) 
    MUST inherit from this to guarantee strict data isolation across the SaaS.
    """
    # By default, enforce authentication on all tenant-aware routes
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Intercept the default DRF queryset and append the tenant filter dynamically.
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, getattr(queryset, 'all', tuple)):
            queryset = queryset.all()

        user = self.request.user

        # Strict Isolation Rule: If the user belongs to a school, only return that school's data.
        if hasattr(user, 'school') and user.school:
            return queryset.filter(school=user.school)
            
        # Security Fallback: If a user somehow has no school assigned (e.g. inactive superuser), 
        # return an empty queryset to prevent cross-tenant data leaks.
        return queryset.none()

    def perform_create(self, serializer):
        """
        Automatically inject the user's school into the created database row
        so the frontend doesn't have to manually pass a school_id in the payload.
        """
        user = self.request.user
        
        if not hasattr(user, 'school') or not user.school:
            raise PermissionDenied("You must be assigned to a school to create records.")
            
        serializer.save(school=user.school)


class CurrentUserView(generics.RetrieveAPIView):
    """
    GET /auth/me/
    Returns the currently authenticated user's details based on their JWT.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user