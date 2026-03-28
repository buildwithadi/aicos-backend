from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenants.views import TenantAwareModelViewSet
from .models import Attendance
from .serializers import AttendanceSerializer, BulkAttendanceSerializer

class AttendanceViewSet(TenantAwareModelViewSet):
    queryset = Attendance.objects.select_related(
        'student__user', 'academic_year', 'class_level', 'section'
    ).all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Allow frontend to filter attendance by date, student, or section dynamically
        date = self.request.query_params.get('date', None)
        student_id = self.request.query_params.get('student', None)
        section_id = self.request.query_params.get('section', None)

        if date:
            qs = qs.filter(date=date)
        if student_id:
            qs = qs.filter(student_id=student_id)
        if section_id:
            qs = qs.filter(section_id=section_id)

        return qs

    @extend_schema(request=BulkAttendanceSerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='bulk-record')
    def bulk_record(self, request):
        """
        POST /api/v1/operations/attendance/bulk-record/
        Highly optimized "Upsert" endpoint for submitting an entire class's attendance.
        If a record for the student/date already exists, it updates it. If not, it creates it.
        """
        serializer = BulkAttendanceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        school = request.user.school

        # Generate the list of Attendance objects in memory
        attendance_objects = []
        for record in data['records']:
            attendance_objects.append(
                Attendance(
                    school=school,
                    academic_year_id=data['academic_year_id'],
                    class_level_id=data['class_level_id'],
                    section_id=data['section_id'],
                    date=data['date'],
                    student_id=record['student_id'],
                    status=record['status'],
                    remarks=record.get('remarks', '')
                )
            )

        # Vectorized SQL Execution (The Pandas way!)
        with transaction.atomic():
            # update_conflicts requires PostgreSQL/SQLite. 
            # It relies entirely on our unique_student_attendance_per_day constraint!
            Attendance.objects.bulk_create(
                attendance_objects,
                update_conflicts=True,
                unique_fields=['school', 'student', 'date'], # The conflict target
                update_fields=['status', 'remarks']          # What to overwrite if conflict occurs
            )

        return Response(
            {"detail": f"Successfully processed attendance for {len(attendance_objects)} students."},
            status=status.HTTP_200_OK
        )