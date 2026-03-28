import uuid
from django.db import models
from tenants.models import TenantAwareModel

class Attendance(TenantAwareModel):
    """
    Tracks daily attendance for students.
    """
    class StatusChoices(models.TextChoices):
        PRESENT = 'Present', 'Present'
        ABSENT = 'Absent', 'Absent'
        LATE = 'Late', 'Late'
        HALF_DAY = 'Half-Day', 'Half-Day'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Using string references to avoid circular imports
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    class_level = models.ForeignKey('academics.ClassLevel', on_delete=models.CASCADE)
    section = models.ForeignKey('academics.Section', on_delete=models.CASCADE)
    
    date = models.DateField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PRESENT)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-date', 'student__user__first_name']
        constraints = [
            # CRITICAL: A student can only have one attendance record per day per school.
            # This enables our optimized "Upsert" logic later.
            models.UniqueConstraint(
                fields=['school', 'student', 'date'], 
                name='unique_student_attendance_per_day'
            )
        ]

    def __str__(self):
        return f"{self.student.user.first_name} - {self.date} ({self.status})"