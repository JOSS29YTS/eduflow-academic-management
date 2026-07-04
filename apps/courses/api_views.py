from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.accounts.models import CustomUser
from .models import Course, Enrollment, Session, Attendance
from .serializers import CourseSerializer, SessionSerializer, EnrollmentSerializer, AttendanceSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows courses to be viewed.
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]:
            return Course.objects.all().order_by('-start_date')
        elif user.role == CustomUser.Role.PROFESSOR:
            return Course.objects.filter(professor=user).order_by('-start_date')
        else:  # STUDENT
            return Course.objects.filter(status=Course.Status.ACTIVE).order_by('-start_date')

    @action(detail=True, methods=['get'], url_path='sessions')
    def sessions(self, request, pk=None):
        """
        List all sessions for a specific course: /api/courses/{id}/sessions/
        """
        course = self.get_object()
        sessions = course.sessions.all().order_by('date', 'start_time')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll(self, request, pk=None):
        """
        Enroll current student in course: /api/courses/{id}/enroll/
        """
        if request.user.role != CustomUser.Role.STUDENT:
            return Response(
                {"detail": "Solo los estudiantes pueden inscribirse en cursos."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        course = self.get_object()
        
        if course.status != Course.Status.ACTIVE:
            return Response(
                {"detail": "Este curso no está activo para inscripciones."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {"detail": "Ya te encuentras registrado en este curso."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check availability
        if not course.has_availability:
            return Response(
                {"detail": "No hay cupos disponibles en este curso."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status=Enrollment.Status.PENDING,
            notes="Inscripción realizada vía API."
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows sessions to be viewed.
    """
    queryset = Session.objects.all().order_by('date', 'start_time')
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get', 'post'], url_path='attendance')
    def attendance(self, request, pk=None):
        """
        Manage attendance for a specific session: /api/sessions/{id}/attendance/
        """
        session = self.get_object()
        user = request.user
        
        # Check permission (only Admin, Coordinator, or course Professor)
        is_admin_coord = user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]
        is_assigned_prof = user.role == CustomUser.Role.PROFESSOR and session.course.professor == user
        
        if not (is_admin_coord or is_assigned_prof):
            return Response(
                {"detail": "No tienes permiso para gestionar la asistencia de esta sesión."},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.method == 'GET':
            # List attendance
            attendances = Attendance.objects.filter(session=session).select_related('student', 'recorded_by')
            serializer = AttendanceSerializer(attendances, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            # Record attendance
            student_id = request.data.get('student_id')
            attendance_status = request.data.get('status')
            notes = request.data.get('notes', '')
            
            if not student_id or not attendance_status:
                return Response(
                    {"detail": "Debe especificar 'student_id' y 'status'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if attendance_status not in [choice[0] for choice in Attendance.Status.choices]:
                return Response(
                    {"detail": f"Status inválido. Opciones válidas: {[choice[0] for choice in Attendance.Status.choices]}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            student = get_object_or_404(CustomUser, pk=student_id)
            
            # Check if student is active enrolled in the course
            is_enrolled = Enrollment.objects.filter(student=student, course=session.course, status=Enrollment.Status.ACTIVE).exists()
            if not is_enrolled:
                return Response(
                    {"detail": "El estudiante no tiene una inscripción activa en este curso."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            attendance, created = Attendance.objects.update_or_create(
                session=session,
                student=student,
                defaults={
                    'status': attendance_status,
                    'notes': notes,
                    'recorded_by': user if user.role == CustomUser.Role.PROFESSOR else None
                }
            )
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows enrollments to be viewed or created.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.Role.STUDENT:
            return Enrollment.objects.filter(student=user).select_related('course').order_by('-enrolled_at')
        else:
            return Enrollment.objects.all().select_related('student', 'course').order_by('-enrolled_at')

    def perform_create(self, serializer):
        # Default self-enrollment if student
        if self.request.user.role == CustomUser.Role.STUDENT:
            serializer.save(student=self.request.user, status=Enrollment.Status.PENDING)
        else:
            # Admins can choose the student via data payload (mapped in validator)
            serializer.save()
