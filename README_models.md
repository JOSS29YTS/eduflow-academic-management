# EduFlow — Modelos de base de datos

## Resumen de modelos

| Modelo | App | Descripción |
|--------|-----|-------------|
| `CustomUser` | accounts | Usuario único con campo `role` (admin/coordinator/professor/student) |
| `Course` | courses | Diplomado o curso con profesor, coordinador, fechas y precio |
| `Enrollment` | courses | Relación M2M con estado entre estudiante y curso |
| `Session` | courses | Clase individual dentro de un curso (cronograma) |
| `Attendance` | courses | Registro de asistencia por sesión y estudiante |
| `Payment` | payments | Pago registrado contra una inscripción |
| `Invoice` | payments | Factura generada automáticamente al confirmar un pago |
| `EmailLog` | payments | Historial de intentos de envío de cada factura |

## Relaciones clave

```
CustomUser (role=professor)
    └── Course.professor → FK
        └── Session → FK
            └── Attendance → FK(session) + FK(student)

CustomUser (role=student)
    └── Enrollment → FK(student) + FK(course)
        └── Payment → FK(enrollment)
            └── Invoice → OneToOne(payment)
                └── EmailLog → FK(invoice)
```

## Estructura de apps Django recomendada

```
eduflow/
├── apps/
│   ├── accounts/       → CustomUser
│   ├── courses/        → Course, Enrollment, Session, Attendance
│   └── payments/       → Payment, Invoice, EmailLog
├── core/               → settings, urls, celery
└── templates/
    ├── invoices/       → plantilla HTML para PDF
    └── emails/         → plantillas de correo
```

## Señales sugeridas (signals.py)

- `post_save` en `Payment` con `status='confirmed'` → crear `Invoice` automáticamente
- `post_save` en `Invoice` → encolar tarea Celery para generar PDF y enviar email
- `post_save` en `Enrollment` con `status='active'` → crear registros `Attendance` vacíos para todas las sesiones del curso

## Índices adicionales recomendados

```python
class Meta:
    indexes = [
        models.Index(fields=['course', 'date']),          # Session
        models.Index(fields=['session', 'student']),      # Attendance
        models.Index(fields=['enrollment', 'status']),    # Payment
        models.Index(fields=['sent_status', 'issued_at']),# Invoice
    ]
```
