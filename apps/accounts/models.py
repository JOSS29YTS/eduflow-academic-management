from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN       = 'admin',       _('Administrador')
        COORDINATOR = 'coordinator', _('Coordinador')
        PROFESSOR   = 'professor',   _('Profesor')
        STUDENT     = 'student',     _('Estudiante')

    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone      = models.CharField(max_length=20, blank=True)
    bio        = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
