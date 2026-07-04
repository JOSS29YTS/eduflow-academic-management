from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from apps.accounts.models import CustomUser
from .models import Course, Enrollment, Session, Attendance


@login_required
def course_list(request):
    """
    List courses depending on the user role.
    """
    user = request.user
    
    if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]:
        courses = Course.objects.all().order_by('-start_date')
    elif user.role == CustomUser.Role.PROFESSOR:
        courses = Course.objects.filter(professor=user).order_by('-start_date')
    else:  # STUDENT
        courses = Course.objects.filter(status=Course.Status.ACTIVE).order_by('-start_date')
        
    # Helper to see which courses a student is enrolled in
    enrolled_course_ids = []
    if user.role == CustomUser.Role.STUDENT:
        enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
        
    context = {
        'courses': courses,
        'enrolled_course_ids': enrolled_course_ids,
    }
    return render(request, 'courses/course_list.html', context)


@login_required
def course_detail(request, course_id):
    """
    Detail page for a specific course.
    """
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    # Check permissions
    if user.role == CustomUser.Role.PROFESSOR and course.professor != user:
        return HttpResponseForbidden("No tienes permiso para ver este curso.")
        
    # Get sessions
    sessions = course.sessions.all().order_by('date', 'start_time')
    
    # Get enrolled students (only for admin/coord/assigned professor)
    show_students = user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR] or (user.role == CustomUser.Role.PROFESSOR and course.professor == user)
    enrollments = []
    if show_students:
        enrollments = course.enrollments.select_related('student').order_by('student__last_name')
        
    # Inscription status for students
    student_enrollment = None
    if user.role == CustomUser.Role.STUDENT:
        student_enrollment = Enrollment.objects.filter(student=user, course=course).first()
        if student_enrollment:
            from .models import Attendance
            attendances = {att.session_id: att for att in Attendance.objects.filter(student=user, session__course=course)}
            for session in sessions:
                session.student_attendance = attendances.get(session.id)
        
    context = {
        'course': course,
        'sessions': sessions,
        'enrollments': enrollments,
        'show_students': show_students,
        'student_enrollment': student_enrollment,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """
    Action for students to enroll in a course.
    """
    if request.user.role != CustomUser.Role.STUDENT:
        return HttpResponseForbidden("Solo los estudiantes pueden inscribirse en cursos.")
        
    course = get_object_or_404(Course, pk=course_id)
    
    if course.status != Course.Status.ACTIVE:
        messages.error(request, "Este curso no se encuentra activo para inscripciones.")
        return redirect('course_detail', course_id=course.id)
        
    # Check if already enrolled
    existing = Enrollment.objects.filter(student=request.user, course=course).exists()
    if existing:
        messages.warning(request, "Ya te encuentras registrado en este curso.")
        return redirect('course_detail', course_id=course.id)
        
    # Check availability
    if not course.has_availability:
        messages.error(request, "Lo sentimos, no hay cupos disponibles en este curso.")
        return redirect('course_detail', course_id=course.id)
        
    # Create enrollment
    Enrollment.objects.create(
        student=request.user,
        course=course,
        status=Enrollment.Status.PENDING,
        notes="Inscripción en línea automática."
    )
    messages.success(request, f"¡Inscripción registrada con éxito en {course.name}! Tu estado está pendiente de pago.")
    return redirect('course_detail', course_id=course.id)


@login_required
def session_attendance(request, session_id):
    """
    Attendance sheet view for a specific session.
    Only accessible by Admins, Coordinators, or the course's assigned Professor.
    """
    session = get_object_or_404(Session, pk=session_id)
    user = request.user
    
    # Check permission
    is_admin_coord = user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]
    is_assigned_prof = user.role == CustomUser.Role.PROFESSOR and session.course.professor == user
    
    if not (is_admin_coord or is_assigned_prof):
        return HttpResponseForbidden("No tienes permiso para gestionar la asistencia de esta sesión.")
        
    # Fetch active enrollments for the course
    enrollments = Enrollment.objects.filter(course=session.course, status=Enrollment.Status.ACTIVE).select_related('student')
    
    # Prepare students list with their corresponding attendance record (get or create)
    students_attendance = []
    for enrollment in enrollments:
        student = enrollment.student
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=student,
            defaults={
                'status': Attendance.Status.ABSENT,
                'recorded_by': user if user.role == CustomUser.Role.PROFESSOR else None
            }
        )
        students_attendance.append({
            'student': student,
            'attendance': attendance
        })
        
    context = {
        'session': session,
        'students_attendance': students_attendance,
    }
    return render(request, 'courses/session_attendance.html', context)


@login_required
def mark_attendance(request, session_id):
    """
    HTMX Ajax endpoint to update attendance for a single student.
    Returns the partial HTML representing the student's row.
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")
        
    session = get_object_or_404(Session, pk=session_id)
    user = request.user
    
    # Check permission
    is_admin_coord = user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]
    is_assigned_prof = user.role == CustomUser.Role.PROFESSOR and session.course.professor == user
    
    if not (is_admin_coord or is_assigned_prof):
        return HttpResponseForbidden("No tienes permiso para modificar esta asistencia.")
        
    student_id = request.POST.get('student_id')
    status = request.POST.get('status')
    
    # Validate inputs
    if not student_id or status not in [choice[0] for choice in Attendance.Status.choices]:
        return HttpResponse("Datos inválidos.", status=400)
        
    student = get_object_or_404(CustomUser, pk=student_id)
    
    # Update or create attendance record
    attendance, created = Attendance.objects.update_or_create(
        session=session,
        student=student,
        defaults={
            'status': status,
            'recorded_by': user if user.role == CustomUser.Role.PROFESSOR else None
        }
    )
    
    # Render and return only the HTMX partial row snippet
    context = {
        'student': student,
        'attendance': attendance,
        'session': session,
    }
    return render(request, 'courses/partials/attendance_row.html', context)
