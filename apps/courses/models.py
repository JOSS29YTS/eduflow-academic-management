from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser
from .managers import EnrollmentQuerySet, AttendanceQuerySet


# ─── Cursos ───────────────────────────────────────────────────────────────────

class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     _('Borrador')
        ACTIVE    = 'active',    _('Activo')
        COMPLETED = 'completed', _('Completado')
        CANCELLED = 'cancelled', _('Cancelado')

    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    professor   = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='courses_teaching',
        limit_choices_to={'role': CustomUser.Role.PROFESSOR}
    )
    coordinator = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='courses_coordinating',
        limit_choices_to={'role__in': [CustomUser.Role.COORDINATOR, CustomUser.Role.ADMIN]}
    )
    price        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_students = models.PositiveIntegerField(default=30)
    start_date   = models.DateField()
    end_date     = models.DateField()
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Curso')
        verbose_name_plural = _('Cursos')
        ordering = ['-start_date', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status=Enrollment.Status.ACTIVE).count()

    @property
    def has_availability(self):
        return self.enrolled_count < self.max_students


# ─── Inscripciones ────────────────────────────────────────────────────────────

class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   _('Pendiente')
        ACTIVE    = 'active',    _('Activo')
        COMPLETED = 'completed', _('Completado')
        WITHDRAWN = 'withdrawn', _('Retirado')

    student     = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='enrollments',
        limit_choices_to={'role': CustomUser.Role.STUDENT}
    )
    course      = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='enrollments')
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    notes       = models.TextField(blank=True)

    objects = EnrollmentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Inscripción')
        verbose_name_plural = _('Inscripciones')
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.full_name} → {self.course.code}"


# ─── Sesiones / Cronograma ────────────────────────────────────────────────────

class Session(models.Model):
    class Status(models.TextChoices):
        SCHEDULED  = 'scheduled',  _('Programada')
        IN_PROGRESS = 'in_progress', _('En curso')
        COMPLETED  = 'completed',  _('Completada')
        CANCELLED  = 'cancelled',  _('Cancelada')

    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    classroom  = models.CharField(max_length=100, blank=True)
    topic      = models.CharField(max_length=300, blank=True)
    notes      = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Sesión')
        verbose_name_plural = _('Sesiones')
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['course', 'date']),
        ]

    def __str__(self):
        return f"{self.course.code} – {self.date} {self.start_time}"


# ─── Asistencia ───────────────────────────────────────────────────────────────

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', _('Presente')
        ABSENT  = 'absent',  _('Ausente')
        LATE    = 'late',    _('Tardanza')
        EXCUSED = 'excused', _('Excusado')

    session     = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    student     = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='attendances',
        limit_choices_to={'role': CustomUser.Role.STUDENT}
    )
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.ABSENT)
    notes       = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True,
        related_name='attendances_recorded',
        limit_choices_to={'role': CustomUser.Role.PROFESSOR}
    )

    objects = AttendanceQuerySet.as_manager()

    class Meta:
        verbose_name = _('Asistencia')
        verbose_name_plural = _('Asistencias')
        unique_together = ('session', 'student')
        ordering = ['session__date', 'student__last_name']
        indexes = [
            models.Index(fields=['session', 'student']),
        ]

    def __str__(self):
        return f"{self.student.full_name} | {self.session} | {self.get_status_display()}"
