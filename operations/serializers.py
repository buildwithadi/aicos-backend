from rest_framework import serializers
from .models import Attendance
from profiles.models import StudentProfile

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.first_name', read_only=True)
    student_enrollment_no = serializers.CharField(source='student.enrollment_number', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ('school', 'id')

# --- BULK ATTENDANCE PAYLOAD DESIGN ---

class AttendanceRecordItemSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=Attendance.StatusChoices.choices)
    remarks = serializers.CharField(max_length=255, required=False, allow_blank=True)

class BulkAttendanceSerializer(serializers.Serializer):
    """
    Validates the payload for submitting an entire class's attendance at once.
    """
    date = serializers.DateField()
    academic_year_id = serializers.UUIDField()
    class_level_id = serializers.UUIDField()
    section_id = serializers.UUIDField()
    records = AttendanceRecordItemSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        request = self.context.get('request')
        school = request.user.school
        
        # Anti-Hijacking: Ensure all students in the payload belong to the admin/teacher's school
        student_ids = [record['student_id'] for record in attrs['records']]
        valid_students_count = StudentProfile.objects.filter(id__in=student_ids, school=school).count()
        
        if valid_students_count != len(student_ids):
            raise serializers.ValidationError("One or more students do not exist or belong to another school.")
            
        return attrs