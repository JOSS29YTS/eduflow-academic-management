<div align="center">

<img src="https://img.shields.io/badge/EduFlow-v1.0-534AB7?style=for-the-badge&logo=graduation-cap" alt="EduFlow v1.0"/>

# EduFlow — Sistema de gestión académica

**Plataforma web completa para la administración de diplomados y cursos:**
pagos, facturación automática, asistencia, cronogramas y roles de usuario.

[**Demo en vivo →**](https://eduflow-demo.up.railway.app) &nbsp;·&nbsp;
[Documentación API](https://eduflow-demo.up.railway.app/api/docs/) &nbsp;·&nbsp;
[Reportar un bug](https://github.com/tu-usuario/eduflow/issues)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat-square&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

</div>

---

## ¿Por qué existe este proyecto?

Durante mi diplomado observé que toda la gestión —pagos, estudiantes, profesores, asistencia— se manejaba en hojas de cálculo Excel, y que las facturas se generaban y enviaban manualmente por correo electrónico.

EduFlow nació para resolver exactamente eso: una aplicación web segura, con roles diferenciados y automatización de los procesos repetitivos.

---

## Capturas de pantalla

> **Nota:** Las imágenes a continuación usan placeholders. Al hacer tu deploy, reemplázalas con capturas reales usando la guía al final de este README.

| Dashboard del administrador | Lista de cursos activos |
|:---:|:---:|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Cursos](docs/screenshots/courses.png) |

| Panel del profesor — pasar asistencia | Factura generada automáticamente |
|:---:|:---:|
| ![Asistencia](docs/screenshots/attendance.png) | ![Factura](docs/screenshots/invoice.png) |

---

## Funcionalidades principales

- **Autenticación con JWT** y cuatro roles: Administrador, Coordinador, Profesor y Estudiante. Cada rol ve solo lo que le corresponde.
- **Gestión de cursos** con inscripción de estudiantes, asignación de profesores y control de cupo máximo.
- **Cronograma de clases** con vista de calendario por curso, estado de cada sesión y sala asignada.
- **Control de asistencia**: los profesores pasan lista directamente desde su panel; el sistema registra presente, ausente, tardanza o excusado.
- **Pagos y facturación automática**: al confirmar un pago, EduFlow genera el PDF de la factura y lo envía por correo sin intervención manual, usando Celery en segundo plano.
- **API REST documentada** con Swagger/OpenAPI para integraciones futuras.

---

## Tecnologías

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje principal |
| Django | 5.0 | Framework web |
| Django REST Framework | 3.15 | API REST |
| SimpleJWT | 5.3 | Autenticación JWT |
| Celery | 5.3 | Tareas asíncronas |
| Redis | 7 | Broker de mensajes para Celery |
| WeasyPrint | 62 | Generación de PDFs |

### Frontend
| Tecnología | Uso |
|---|---|
| Tailwind CSS 3.4 | Estilos utilitarios |
| HTMX | Interactividad sin JavaScript complejo |
| Alpine.js | Componentes reactivos ligeros |
| Django Templates | Renderizado server-side |

### Infraestructura
| Tecnología | Uso |
|---|---|
| PostgreSQL 16 | Base de datos principal |
| Docker + Docker Compose | Contenedorización |
| Railway | Deploy en producción |
| GitHub Actions | CI/CD |
| Cloudflare R2 / S3 | Almacenamiento de PDFs |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                        Cliente                          │
│              (Django Templates + HTMX)                  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / JSON
┌────────────────────────▼────────────────────────────────┐
│                    Django 5 + DRF                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ accounts │  │ courses  │  │payments  │  │  API   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
└────────┬──────────────────────────────┬─────────────────┘
         │                              │
┌────────▼──────────┐        ┌──────────▼──────────────┐
│   PostgreSQL 16   │        │  Celery + Redis          │
│   (datos)         │        │  · generar PDF           │
└───────────────────┘        │  · enviar email          │
                             └─────────────────────────┘
```

### Estructura de apps Django

```
eduflow/
├── apps/
│   ├── accounts/       # CustomUser, roles, JWT
│   ├── courses/        # Course, Enrollment, Session, Attendance
│   └── payments/       # Payment, Invoice, EmailLog
├── core/               # settings, urls, celery.py
├── templates/
│   ├── invoices/       # plantilla HTML → PDF
│   └── emails/         # plantillas de correo
├── static/
└── docker-compose.yml
```

---

## Modelo de datos

El esquema completo con 8 modelos y sus relaciones está documentado en [`docs/database.md`](docs/database.md).

Relación principal:

```
CustomUser (role=student)
  └── Enrollment ──────────► Course ◄── CustomUser (role=professor)
        └── Payment                         └── Session
              └── Invoice                         └── Attendance
                    └── EmailLog
```

---

## Instalación local

### Prerrequisitos

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Node.js 20+ (para compilar Tailwind)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/eduflow.git
cd eduflow

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL, Redis y SMTP

# 4. Aplicar migraciones y cargar datos de ejemplo
python manage.py migrate
python manage.py loaddata fixtures/demo_data.json

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Compilar estilos Tailwind
npm install
npm run build:css

# 7. Iniciar el servidor de desarrollo
python manage.py runserver
```

Luego abre [http://localhost:8000](http://localhost:8000).

### Con Docker (recomendado)

```bash
git clone https://github.com/tu-usuario/eduflow.git
cd eduflow
cp .env.example .env
docker compose up --build
```

Todos los servicios (Django, PostgreSQL, Redis, Celery) arrancan automáticamente.

---

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
# Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,tu-dominio.com

# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/eduflow

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=tu-api-key
DEFAULT_FROM_EMAIL=noreply@tu-dominio.com

# Almacenamiento (opcional, para producción)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
```

---

## API REST

La API está documentada con Swagger en `/api/docs/` y con ReDoc en `/api/redoc/`.

Endpoints principales:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/auth/token/` | Obtener tokens JWT |
| `POST` | `/api/auth/token/refresh/` | Renovar access token |
| `GET` | `/api/courses/` | Listar cursos (filtrado por rol) |
| `GET` | `/api/courses/{id}/sessions/` | Sesiones de un curso |
| `POST` | `/api/sessions/{id}/attendance/` | Registrar asistencia |
| `GET` | `/api/enrollments/` | Inscripciones del usuario |
| `POST` | `/api/payments/` | Registrar un pago |
| `GET` | `/api/invoices/{id}/pdf/` | Descargar factura en PDF |

Ejemplo de autenticación:

```bash
# Obtener token
curl -X POST https://eduflow-demo.up.railway.app/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo_admin", "password": "demo1234"}'

# Usar el token en solicitudes protegidas
curl https://eduflow-demo.up.railway.app/api/courses/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Usuarios de demostración

La base de datos demo incluye estos usuarios de prueba:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `demo_admin` | `demo1234` |
| Coordinador | `demo_coord` | `demo1234` |
| Profesor | `demo_profesor` | `demo1234` |
| Estudiante | `demo_estudiante` | `demo1234` |

---

## Deploy en Railway

Este proyecto está configurado para deploy con un solo clic en Railway:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/eduflow)

O manualmente:

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

El `Procfile` y `railway.json` incluidos configuran automáticamente Django, Celery y los workers.

---

## Contribuir

Las contribuciones son bienvenidas. Para cambios grandes, abre primero un issue para discutir qué te gustaría modificar.

```bash
# Fork del repo → clonar tu fork
git checkout -b feature/nombre-de-tu-feature
git commit -m "feat: descripción del cambio"
git push origin feature/nombre-de-tu-feature
# Abrir Pull Request
```

Este proyecto usa [Conventional Commits](https://www.conventionalcommits.org/es/).

---

## Cómo agregar capturas de pantalla reales

Una vez que tu proyecto esté desplegado:

1. Crea la carpeta `docs/screenshots/` en tu repositorio.
2. Toma capturas con una resolución de 1280×800 px mínimo.
3. Optimiza las imágenes: `npx sharp-cli input.png -o output.png --resize 1280`
4. Nómbralas igual que las referencias en este README: `dashboard.png`, `courses.png`, `attendance.png`, `invoice.png`.
5. Haz commit y push — GitHub las mostrará automáticamente.

Para el GIF animado del hero (opcional pero muy llamativo):

```bash
# Instalar LICEcap (Windows/Mac) o Peek (Linux)
# Graba el flujo: login → dashboard → pasar asistencia → ver factura
# Guarda como docs/screenshots/demo.gif
```

---

## Licencia

Distribuido bajo la licencia MIT. Ver [`LICENSE`](LICENSE) para más información.

---

<div align="center">

Desarrollado por **[Tu Nombre]** como proyecto final de diplomado · 2026

[LinkedIn](https://linkedin.com/in/tu-usuario) &nbsp;·&nbsp; [Portafolio](https://tu-sitio.com) &nbsp;·&nbsp; [GitHub](https://github.com/tu-usuario)

</div>
