import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.courses.models import Course, Enrollment, Session, Attendance
from apps.payments.models import Payment, Invoice, EmailLog


class Command(BaseCommand):
    help = 'Populates the database with initial demo data for EduFlow'

    def handle(self, *args, **options):
        self.stdout.write('Generating demo data...')

        # 1. Create Users
        # Admin
        admin_user, created = CustomUser.objects.get_or_create(
            username='demo_admin',
            defaults={
                'email': 'admin@eduflow.com',
                'first_name': 'Carlos',
                'last_name': 'Administrador',
                'role': CustomUser.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('demo1234')
            admin_user.save()
            self.stdout.write('Created user demo_admin')

        # Coordinator
        coord_user, created = CustomUser.objects.get_or_create(
            username='demo_coord',
            defaults={
                'email': 'coord@eduflow.com',
                'first_name': 'Ana',
                'last_name': 'Coordinadora',
                'role': CustomUser.Role.COORDINATOR,
                'is_staff': True
            }
        )
        if created:
            coord_user.set_password('demo1234')
            coord_user.save()
            self.stdout.write('Created user demo_coord')

        # Professor
        prof_user, created = CustomUser.objects.get_or_create(
            username='demo_profesor',
            defaults={
                'email': 'profesor@eduflow.com',
                'first_name': 'Roberto',
                'last_name': 'Profesor',
                'role': CustomUser.Role.PROFESSOR
            }
        )
        if created:
            prof_user.set_password('demo1234')
            prof_user.save()
            self.stdout.write('Created user demo_profesor')

        # Student 1
        student_user, created = CustomUser.objects.get_or_create(
            username='demo_estudiante',
            defaults={
                'email': 'estudiante@eduflow.com',
                'first_name': 'Lucía',
                'last_name': 'Estudiante',
                'role': CustomUser.Role.STUDENT
            }
        )
        if created:
            student_user.set_password('demo1234')
            student_user.save()
            self.stdout.write('Created user demo_estudiante')

        # Student 2
        student_user2, created = CustomUser.objects.get_or_create(
            username='estudiante2',
            defaults={
                'email': 'estudiante2@eduflow.com',
                'first_name': 'Mateo',
                'last_name': 'Gómez',
                'role': CustomUser.Role.STUDENT
            }
        )
        if created:
            student_user2.set_password('demo1234')
            student_user2.save()
            self.stdout.write('Created user estudiante2')

        # 2. Create Courses
        course_active, created = Course.objects.get_or_create(
            code='DJ-01',
            defaults={
                'name': 'Diplomado en Desarrollo Web con Django & React',
                'description': 'Aprende a desarrollar aplicaciones web modernas desde cero.',
                'professor': prof_user,
                'coordinator': coord_user,
                'price': 350.00,
                'max_students': 20,
                'start_date': datetime.date.today() - datetime.timedelta(days=10),
                'end_date': datetime.date.today() + datetime.timedelta(days=50),
                'status': Course.Status.ACTIVE
            }
        )
        if created:
            self.stdout.write('Created course DJ-01')

        course_draft, created = Course.objects.get_or_create(
            code='AI-02',
            defaults={
                'name': 'Diplomado en Inteligencia Artificial y Machine Learning',
                'description': 'Introducción a redes neuronales, deep learning y NLP.',
                'professor': prof_user,
                'coordinator': admin_user,
                'price': 500.00,
                'max_students': 15,
                'start_date': datetime.date.today() + datetime.timedelta(days=20),
                'end_date': datetime.date.today() + datetime.timedelta(days=80),
                'status': Course.Status.DRAFT
            }
        )
        if created:
            self.stdout.write('Created course AI-02')

        # 3. Create Sessions for Active Course
        session1, created = Session.objects.get_or_create(
            course=course_active,
            date=datetime.date.today() - datetime.timedelta(days=2),
            defaults={
                'start_time': datetime.time(19, 0),
                'end_time': datetime.time(21, 30),
                'classroom': 'Aula Virtual 101',
                'topic': 'Introducción a Django: Configuración de Entorno',
                'status': Session.Status.COMPLETED
            }
        )
        if created:
            self.stdout.write('Created session 1')

        session2, created = Session.objects.get_or_create(
            course=course_active,
            date=datetime.date.today() + datetime.timedelta(days=5),
            defaults={
                'start_time': datetime.time(19, 0),
                'end_time': datetime.time(21, 30),
                'classroom': 'Aula Virtual 101',
                'topic': 'Modelos y ORM de Django: Diseño de Base de Datos',
                'status': Session.Status.SCHEDULED
            }
        )
        if created:
            self.stdout.write('Created session 2')

        # 4. Create Enrollments
        enrollment1, created = Enrollment.objects.get_or_create(
            student=student_user,
            course=course_active,
            defaults={
                'status': Enrollment.Status.ACTIVE,
                'notes': 'Pago inicial completado por transferencia.'
            }
        )
        if created:
            self.stdout.write('Enrolled demo_estudiante in DJ-01')

        enrollment2, created = Enrollment.objects.get_or_create(
            student=student_user2,
            course=course_active,
            defaults={
                'status': Enrollment.Status.PENDING,
                'notes': 'Pendiente por confirmación de pago.'
            }
        )
        if created:
            self.stdout.write('Enrolled estudiante2 in DJ-01')

        # 5. Create Attendance for session 1
        att1, created = Attendance.objects.get_or_create(
            session=session1,
            student=student_user,
            defaults={
                'status': Attendance.Status.PRESENT,
                'recorded_by': prof_user,
                'notes': 'Llegó a tiempo'
            }
        )
        if created:
            self.stdout.write('Recorded attendance present for student 1')

        att2, created = Attendance.objects.get_or_create(
            session=session1,
            student=student_user2,
            defaults={
                'status': Attendance.Status.ABSENT,
                'recorded_by': prof_user,
                'notes': 'No se conectó a la sesión virtual'
            }
        )
        if created:
            self.stdout.write('Recorded attendance absent for student 2')

        # 6. Create Payments & Invoices
        payment1, created = Payment.objects.get_or_create(
            enrollment=enrollment1,
            amount=150.00,
            defaults={
                'payment_method': Payment.Method.TRANSFER,
                'status': Payment.Status.CONFIRMED,
                'payment_date': datetime.date.today() - datetime.timedelta(days=9),
                'reference_number': 'TX-9988223',
                'recorded_by': admin_user,
                'notes': 'Matrícula y primera cuota.'
            }
        )
        if created:
            self.stdout.write('Created payment of 150.00')

            # Create Invoice for confirmed payment
            invoice1, created_inv = Invoice.objects.get_or_create(
                payment=payment1,
                defaults={
                    'recipient_email': student_user.email,
                    'sent_status': Invoice.SentStatus.SENT,
                    'sent_at': timezone.now()
                }
            )
            if created_inv:
                self.stdout.write(f'Generated invoice {invoice1.invoice_number} for payment')
                # Create Email Log
                EmailLog.objects.create(
                    invoice=invoice1,
                    recipient=student_user.email,
                    subject=f'Factura de Inscripción {invoice1.invoice_number}',
                    status=EmailLog.Status.SENT,
                    sent_at=timezone.now()
                )
                self.stdout.write('Created email log for invoice')

        self.stdout.write(self.style.SUCCESS('Successfully loaded all demo data!'))
