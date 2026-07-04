from django.db import models


class EnrollmentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status='active')

    def for_professor(self, user):
        return self.filter(course__professor=user)

    def for_student(self, user):
        return self.filter(student=user)


class AttendanceQuerySet(models.QuerySet):
    def for_session(self, session):
        return self.filter(session=session)

    def present(self):
        return self.filter(status='present')

    def attendance_rate(self):
        total = self.count()
        if total == 0:
            return 0
        present = self.filter(status__in=['present', 'late']).count()
        return round((present / total) * 100, 1)
