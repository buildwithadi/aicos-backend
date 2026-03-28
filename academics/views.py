from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenants.views import TenantAwareModelViewSet
from .models import StudentEnrollment, TeacherAssignment
from .serializers import StudentEnrollmentSerializer, TeacherAssignmentSerializer, BulkPromotionSerializer

class StudentEnrollmentViewSet(TenantAwareModelViewSet):
    queryset = StudentEnrollment.objects.select_related(
        'student__user', 'academic_year', 'class_level', 'section'
    ).all()
    serializer_class = StudentEnrollmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        student_id = self.request.query_params.get('student', None)

        if student_id:
            qs = qs.filter(student_id=student_id)

        today = timezone.now().date()
        if status_param == 'current':
            qs = qs.filter(
                academic_year__start_date__lte=today,
                academic_year__end_date__gte=today
            )
        elif status_param == 'historical':
            qs = qs.filter(academic_year__end_date__lt=today)

        return qs

    # --- NEW ENDPOINT FOR TASK 3.4 ---
    @extend_schema(request=BulkPromotionSerializer, responses={201: dict})
    @action(detail=False, methods=['post'], url_path='bulk-promote')
    def bulk_promote(self, request):
        """
        POST /api/v1/academics/enrollments/bulk-promote/
        Promotes a batch of students to a new class/section for a new academic year.
        """
        serializer = BulkPromotionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        school = request.user.school
        student_ids = data['student_ids']

        # Prepare objects for bulk insertion
        enrollments_to_create = []
        for student_id in student_ids:
            enrollments_to_create.append(
                StudentEnrollment(
                    school=school,
                    student_id=student_id,
                    academic_year_id=data['target_academic_year_id'],
                    class_level_id=data['target_class_level_id'],
                    section_id=data['target_section_id']
                )
            )

        try:
            # transaction.atomic() ensures that if one fails, NONE are saved.
            with transaction.atomic():
                # bulk_create writes all rows in a single SQL query (highly optimized!)
                StudentEnrollment.objects.bulk_create(enrollments_to_create)
                
            return Response(
                {"detail": f"Successfully promoted {len(student_ids)} students."},
                status=status.HTTP_201_CREATED
            )
            
        except IntegrityError:
            # Catches the unique_student_enrollment_per_year constraint
            return Response(
                {"detail": "Promotion failed. One or more students are already enrolled in the target academic year."},
                status=status.HTTP_400_BAD_REQUEST
            )

class TeacherAssignmentViewSet(TenantAwareModelViewSet):
    queryset = TeacherAssignment.objects.select_related(
        'teacher__user', 'academic_year', 'class_level', 'section', 'subject'
    ).all()
    serializer_class = TeacherAssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        teacher_id = self.request.query_params.get('teacher', None)

        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)

        today = timezone.now().date()
        if status_param == 'current':
            qs = qs.filter(
                academic_year__start_date__lte=today,
                academic_year__end_date__gte=today
            )
        elif status_param == 'historical':
            qs = qs.filter(academic_year__end_date__lt=today)

        return qs