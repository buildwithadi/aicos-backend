from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentEnrollmentViewSet, TeacherAssignmentViewSet

router = DefaultRouter()
router.register(r'enrollments', StudentEnrollmentViewSet, basename='enrollment')
router.register(r'teacher-assignments', TeacherAssignmentViewSet, basename='teacher-assignment')

urlpatterns = [
    path('', include(router.urls)),
]   