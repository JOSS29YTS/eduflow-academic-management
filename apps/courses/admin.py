from django.contrib import admin
from .models import Course, Enrollment, Session, Attendance


class EnrollmentInline(admin.TabularInline):
    model  = Enrollment
    extra  = 0
    fields = ('student', 'status', 'enrolled_at')
    readonly_fields = ('enrolled_at',)


class SessionInline(admin.TabularInline):
    model  = Session
    extra  = 0
    fields = ('date', 'start_time', 'end_time', 'classroom', 'topic', 'status')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display   = ('code', 'name', 'professor', 'start_date', 'end_date', 'enrolled_count', 'status')
    list_filter    = ('status', 'start_date')
    search_fields  = ('name', 'code')
    inlines        = [EnrollmentInline, SessionInline]
    readonly_fields = ('enrolled_count',)


class AttendanceInline(admin.TabularInline):
    model  = Attendance
    extra  = 0
    fields = ('student', 'status', 'notes')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'start_time', 'classroom', 'topic', 'status')
    list_filter  = ('status', 'date', 'course')
    inlines      = [AttendanceInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ('student', 'course', 'status', 'enrolled_at')
    list_filter   = ('status', 'course')
    search_fields = ('student__username', 'student__email', 'course__name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('student', 'session', 'status', 'recorded_by', 'recorded_at')
    list_filter   = ('status', 'session__course')
    search_fields = ('student__username',)
