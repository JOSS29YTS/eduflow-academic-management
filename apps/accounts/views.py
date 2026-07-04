from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.models import CustomUser
from apps.accounts.forms import StudentSignUpForm, UserProfileForm
from apps.courses.models import Course, Enrollment, Session, Attendance
from apps.payments.models import Payment, Invoice


@login_required
def dashboard_redirect(request):
    """
    Redirects user to the correct dashboard based on their role
    and injects role-specific context.
    """
    user = request.user
    
    if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.COORDINATOR]:
        # --- ADMIN / COORDINATOR DASHBOARD ---
        total_courses = Course.objects.count()
        total_students = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count()
        total_revenue = Payment.objects.confirmed().total_amount()
        active_enrollments = Enrollment.objects.active().count()
        
        # Recent activity lists
        recent_payments = Payment.objects.select_related('enrollment__student', 'enrollment__course').order_by('-created_at')[:5]
        recent_courses = Course.objects.select_related('professor').order_by('-created_at')[:5]
        
        context = {
            'total_courses': total_courses,
            'total_students': total_students,
            'total_revenue': total_revenue,
            'active_enrollments': active_enrollments,
            'recent_payments': recent_payments,
            'recent_courses': recent_courses,
        }
        return render(request, 'accounts/dashboard_admin.html', context)
        
    elif user.role == CustomUser.Role.PROFESSOR:
        # --- PROFESSOR DASHBOARD ---
        courses = Course.objects.filter(professor=user).order_by('-start_date')
        
        # Get active sessions of professor's courses
        sessions = Session.objects.filter(course__professor=user).select_related('course').order_by('date', 'start_time')
        upcoming_sessions = sessions.filter(date__gte=timezone_today())[:5]
        
        # Calculate totals
        total_my_courses = courses.count()
        total_my_sessions = sessions.count()
        
        context = {
            'courses': courses,
            'upcoming_sessions': upcoming_sessions,
            'total_my_courses': total_my_courses,
            'total_my_sessions': total_my_sessions,
        }
        return render(request, 'accounts/dashboard_professor.html', context)
        
    elif user.role == CustomUser.Role.STUDENT:
        # --- STUDENT DASHBOARD ---
        enrollments = Enrollment.objects.filter(student=user).select_related('course')
        
        # Calculate attendance rate
        student_attendances = Attendance.objects.filter(student=user)
        total_classes = student_attendances.count()
        present_classes = student_attendances.filter(status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]).count()
        attendance_rate = round((present_classes / total_classes) * 100, 1) if total_classes > 0 else 0
        
        # Get payments
        payments = Payment.objects.filter(enrollment__student=user).select_related('enrollment__course').order_by('-payment_date')
        
        context = {
            'enrollments': enrollments,
            'attendance_rate': attendance_rate,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'payments': payments,
        }
        return render(request, 'accounts/dashboard_student.html', context)

    # Fallback redirect to login
    return redirect('login')


def student_signup(request):
    """
    Student registration view.
    Saves the user as is_active = False for admin approval.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                "¡Registro exitoso! Tu cuenta ha sido creada y está en proceso de revisión. "
                "Un administrador debe habilitarla antes de que puedas iniciar sesión."
            )
            return redirect('login')
    else:
        form = StudentSignUpForm()
        
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def user_profile(request):
    """
    View to edit profile details of the logged-in user.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado con éxito.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'accounts/profile.html', {'form': form})


def timezone_today():
    """Helper to return current date in local timezone"""
    from django.utils import timezone
    return timezone.localdate()
