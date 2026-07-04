from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Enrollment, Attendance, Session


@receiver(post_save, sender=Enrollment)
def auto_create_attendances_on_active_enrollment(sender, instance, created, **kwargs):
    """
    When an Enrollment is set to ACTIVE, pre-populate empty attendance records (ABSENT)
    for all existing sessions of the course for this student.
    """
    if instance.status == Enrollment.Status.ACTIVE:
        sessions = Session.objects.filter(course=instance.course)
        for session in sessions:
            # Get or create to avoid duplicate constraint errors
            Attendance.objects.get_or_create(
                session=session,
                student=instance.student,
                defaults={
                    'status': Attendance.Status.ABSENT,
                    'recorded_by': None
                }
            )
