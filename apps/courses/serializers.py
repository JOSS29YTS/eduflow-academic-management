from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Course, Enrollment, Session, Attendance


class CourseSerializer(serializers.ModelSerializer):
    professor = UserSerializer(read_only=True)
    coordinator = UserSerializer(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    has_availability = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'name', 'code', 'description', 'professor', 'coordinator', 
            'price', 'max_students', 'start_date', 'end_date', 'status',
            'enrolled_count', 'has_availability'
        )


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ('id', 'course', 'date', 'start_time', 'end_time', 'classroom', 'topic', 'notes', 'status')


class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source='course', write_only=True
    )

    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'course', 'course_id', 'status', 'enrolled_at', 'notes')
        read_only_fields = ('id', 'student', 'status', 'enrolled_at')


class AttendanceSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ('id', 'session', 'student', 'status', 'notes', 'recorded_by', 'recorded_at')
        read_only_fields = ('id', 'recorded_by', 'recorded_at')
