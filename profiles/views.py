from rest_framework import viewsets, views, response
from rest_framework.permissions import IsAuthenticated
from tenants.views import TenantAwareModelViewSet
from .models import StudentProfile, TeacherProfile, ParentProfile, ParentStudentMapping
from .serializers import (
    StudentProfileSerializer, TeacherProfileSerializer, 
    ParentProfileSerializer, ParentStudentMappingSerializer
)

# --- TASK 2.3: Profile APIs ---

class StudentProfileViewSet(TenantAwareModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer

class TeacherProfileViewSet(TenantAwareModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer

class ParentProfileViewSet(TenantAwareModelViewSet):
    queryset = ParentProfile.objects.all()
    serializer_class = ParentProfileSerializer

class ParentStudentMappingViewSet(TenantAwareModelViewSet):
    queryset = ParentStudentMapping.objects.all()
    serializer_class = ParentStudentMappingSerializer

# --- TASK 2.4: Context Switching API ---

class UserContextView(views.APIView):
    """
    GET /api/v1/profiles/me/
    Returns the user's base identity, their RBAC roles, and any 
    linked profiles (Teacher, Parent, Student) for frontend context switching.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Fetch any linked profiles for this user
        student_profile = StudentProfile.objects.filter(user=user).first()
        teacher_profile = TeacherProfile.objects.filter(user=user).first()
        parent_profile = ParentProfile.objects.filter(user=user).first()

        # 2. Fetch active roles from the RBAC engine (Accounts App)
        # Using a safe fallback in case user_roles isn't defined properly yet
        roles = []
        if hasattr(user, 'user_roles'):
            roles = list(user.user_roles.filter(school=user.school).values_list('role__name', flat=True))

        # 3. Construct the Context Payload
        payload = {
            "identity": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "school_id": user.school_id,
            },
            "roles": roles,
            "is_superuser": user.is_superuser,
            "profiles": {
                "student": {
                    "exists": bool(student_profile),
                    "id": student_profile.id if student_profile else None,
                },
                "teacher": {
                    "exists": bool(teacher_profile),
                    "id": teacher_profile.id if teacher_profile else None,
                },
                "parent": {
                    "exists": bool(parent_profile),
                    "id": parent_profile.id if parent_profile else None,
                }
            }
        }
        
        return response.Response(payload)