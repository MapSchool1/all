# Matute Guide

> **Plataforma escolar integral para la red Universidad de Guadalajara.**
> Reemplaza procesos manuales dispersos con una sola app: navegación del campus, horarios con detección de conflictos, calificaciones, asistencia, trámites en línea, anuncios y panel administrativo.

[![Tests](https://img.shields.io/badge/tests-58_passing-success)]()
[![Backend](https://img.shields.io/badge/backend-Flask_3-blue)]()
[![Mobile](https://img.shields.io/badge/mobile-Flutter_3.41_APK-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Design](https://img.shields.io/badge/design-MapSchool_v1-172846)]()

---

## ¿Qué resuelve?

Hoy en CUValles cada cosa vive en un lado distinto: el horario impreso, el kárdex en una ventanilla, el mapa en un PDF, los anuncios en un grupo de WhatsApp. **Matute Guide unifica todo en una sola plataforma**, accesible desde la web y desde una app Android.

| Antes | Con Matute Guide |
|---|---|
| Llegar al salón equivocado porque el horario está desactualizado | Horario en tiempo real con detección automática de conflictos |
| Perderse buscando un edificio | Mapa interactivo del campus con cómo-llegar |
| Hacer fila para una constancia | Trámites en línea con folio y seguimiento |
| Enterarte tarde de un parcial | Notificaciones push + en-app de cada cambio |
| Llamar al coordinador para preguntar tu calificación | Calificaciones publicadas y visibles para el estudiante |
| El admin maneja todo en Excel | Panel con KPIs, CRUD y export CSV |

---

## En 30 segundos

```
┌────────────────────────────────────────────────────────────────────┐
│  WEB (Flask + Jinja)              MÓVIL (Flutter Android)          │
│  ┌──────────────────────┐         ┌────────────────────┐           │
│  │ Estudiante           │         │ Login              │           │
│  │  · Dashboard 5 tabs  │         │ Dashboard          │           │
│  │  · Horario builder   │ ◄──┐    │ Horario scrollable │           │
│  │  · Inscripciones     │    │    │ Salones + Mapa     │           │
│  │  · Trámites          │    │    │ Calif/Asistencia   │           │
│  └──────────────────────┘    │    │ Trámites           │           │
│  ┌──────────────────────┐    │    │ Notifs (local)     │           │
│  │ Profesor             │    │    └─────────┬──────────┘           │
│  │  · Pasar lista       │    │              │                      │
│  │  · Capturar calif.   │    │              │ Bearer JWT           │
│  └──────────────────────┘    │              │                      │
│  ┌──────────────────────┐    │              ▼                      │
│  │ Admin                │    │    ┌────────────────────────────┐   │
│  │  · KPIs dashboard    │    └────► Backend Flask              │   │
│  │  · CRUD usuarios     │  Cookies │ · 13 blueprints API       │   │
│  │  · Horarios 3 vistas │  httpOnly│ · 19 modelos SQLAlchemy   │   │
│  │  · Reportes CSV      │  + sesión│ · JWT 1h+30d con rotación │   │
│  │  · Audit log         │          │ · Audit log + Soft-delete │   │
│  └──────────────────────┘          │ · SSE notificaciones      │   │
│                                    │ · Rate limit + CORS       │   │
│                                    │ · SQLite dev / Postgres   │   │
│                                    │   prod                    │   │
│                                    └───────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Pruébalo en 3 minutos

### Web (backend + admin/estudiante)

```bash
# 1) Clonar y entrar al proyecto
git clone https://github.com/MapSchool1/web.git matute-guide
cd matute-guide

# 2) Instalar dependencias Python en un venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3) Poblar la base de datos con datos realistas
python seed.py
#   → 1 plantel, 3 carreras, 44 salones, 72 materias,
#     12 usuarios, horario completo de Álvaro CON conflicto Mié 11:00

# 4) Levantar el servidor
python run.py
#   → http://localhost:5001
```

### App Android (opcional)

```bash
cd flutter_app
flutter pub get

# Lanzar emulador y correr
flutter emulators --launch <id>
flutter run --dart-define=API_BASE=http://10.0.2.2:5001

# O construir APK release
flutter build apk --release --target-platform android-arm64
#   → build/app/outputs/flutter-apk/app-release.apk (~19 MB)
```

---

## Cuentas de demo

Todas las cuentas están en `seed.py`. La interesante es **Álvaro** porque su horario tiene un **conflicto real el miércoles 11:00** (Programación Web LAB-4 vs Bases de Datos II LAB-2) — sirve para validar que la detección automática funciona.

| Email | Password | Rol | Lo que verás |
|---|---|---|---|
| `admin@udg.mx` | `Admin1234!` | admin | Panel con KPIs · CRUD usuarios · 3 vistas de horarios · export CSV |
| `cristina.aguirre@udg.mx` | `Director1!` | director | Mismo panel, alcance plantel |
| `coordinador@udg.mx` | `Coordinador1!` | coordinador | Mismo panel, alcance departamento |
| **`alvaro.diaz@alumnos.udg.mx`** | **`Estudiante1!`** | estudiante | Dashboard 4° Informática **con conflicto Mié 11:00** ⚠ |
| `yael.vega@alumnos.udg.mx` | `Estudiante1!` | estudiante | 2° Biotecnología |
| `rocio.castellanos@alumnos.udg.mx` | `Estudiante1!` | estudiante | 6° Energías |
| `jorge.mendez@udg.mx` | `Profesor1!` | profesor | Cálculo I — pasa lista, captura calificaciones |
| 5 profesores más | `Profesor1!` | profesor | — |

---

## Lo que tiene dentro

### Backend (Flask · 37 archivos Python)

| Capa | Qué hace |
|---|---|
| **`app/api/`** — 13 blueprints REST | auth · users · academic · campus · horarios · inscripciones · tramites · notifications (SSE) · stats · mapa · search · audit · anuncios |
| **`app/web/`** — vistas Jinja | landing · auth · student · profesor · admin · components-demo |
| **`app/models/`** — 19 modelos SQLAlchemy en 7 dominios | usuarios (con soft-delete) · académico · campus · horarios (con detección de conflictos) · inscripciones · trámites · notificaciones |
| **`app/utils/`** | `roles_required` decorator · pagination · audit log helper · `notify()` · `detectar_conflictos_horario()` |
| **`seed.py`** | Datos realistas reproducibles — incluye conflicto intencional para QA |

**Endurecimiento de seguridad incluido**:
- JWT access 1h + refresh 30d con **rotación automática y blacklist**
- En web: cookies **httpOnly + SameSite=Lax** + sesión Flask. En APK: Bearer header
- Bcrypt cost factor 12 · Rate limit 10/min en login · CORS explícito
- Audit log inmutable de cada acción privilegiada (`user.delete`, `horario.publish`, etc.)
- Soft-delete en usuarios/horarios/materias — nunca `DROP`
- Headers `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- Password reset con token 1h + revocación de todas las sesiones al cambiar

### Web (45 plantillas Jinja · cero hex hardcoded)

- **Sistema de diseño MapSchool v1**: tokens CSS (`navy #172846`, Lexend / DM Sans / DM Mono, grid 4px, **WCAG AA**)
- **27 componentes reusables** como macros Jinja: Button×6 · Input · Switch · StatusBadge · RoleTag · Avatar · Tabs · Alert×4 · Toast (auto-dismiss) · Dialog×2 · Dropdown · Tooltip · Breadcrumbs · Pagination · Cards · StatCard · DataTable · EmptyState · ScheduleGrid
- **Página `/components`** (sólo en `DEBUG=True`) con los 21 componentes en vivo usando datos reales del seed
- **Notificaciones en tiempo real** vía SSE — bell badge actualiza sin recargar
- **Mapa SVG interactivo** con click en edificios y "¿Cómo llegar?" textual
- Accesibilidad: skip-link, `aria-*` en todos los botones de iconos, `Esc` cierra paneles, focus visible 3px navy

### App Android (Flutter 3.41 · 36 archivos Dart · 0 `Color(0xFF...)` inline)

- **21 pantallas**: Login · Register · Dashboard (5 tabs) · Horario · Salones · SalonDetail · Mapa (InteractiveViewer) · Calificaciones · Asistencia · Trámites · Perfil · Profesor · Admin (Drawer + KPIs) · AdminUsuarios · AdminHorarios · AdminSalones · Notificaciones
- **GoRouter** con auth guard · **Provider** para estado · **ApiService** con interceptor 401→refresh→retry→logout
- **Notificaciones locales** vía `flutter_local_notifications` con polling 30s
- Espejo del design system: `MapColors`/`MapText` con los mismos hex que `tokens.css`
- **APK release ~19 MB** con desugaring + minSdk 21

### Tests (58 totales — todos verde)

| Tipo | Archivos | Cobertura |
|---|---|---|
| **Pytest** (backend) | `tests/test_health.py` · `test_auth.py` · `test_salones.py` · `test_horarios.py` | health · login + roles + refresh · salones · conflicto Mié 11:00 + dashboard |
| **Dart unit** | `test/models/*_test.dart` × 4 | AppUser · Bloque · Salon · Horario.fromResponse |
| **Flutter widget** | `test/widgets/*_test.dart` × 4 | AppAvatar · StatusBadge · StatCard · ScheduleGrid (con tap callback) |
| **Flutter integration** | `integration_test/login_flow_test.dart` | Login → Dashboard → Conflicto visible (E2E) |

```bash
# Correr toda la suite
source .venv/bin/activate && pytest -q                    # Backend (15 tests)
cd flutter_app && flutter test test/                       # Dart (43 tests)
flutter test integration_test/login_flow_test.dart \      # E2E (requiere backend up)
  --dart-define=API_BASE=http://10.0.2.2:5001
```

---

## Reglas absolutas del proyecto

Las que no se rompen, sin excepción:

1. **Cero datos hardcodeados.** Todo viene de la BD vía API.
2. **Cero colores hardcodeados.** Web usa `var(--token)`, Flutter usa `MapColors.*`.
3. **Copy en español**, segunda persona, acentos correctos.
4. **WCAG AA** en todos los pares texto/fondo.
5. **Cada vista** tiene su empty state.
6. **Cada formulario** tiene validación inline.
7. **Soft-delete** para entidades críticas. Nunca `DROP`.
8. **Audit log** para cada operación destructiva o privilegiada.

---

## API destacados

```bash
# Health check
curl http://localhost:5001/health

# Login (devuelve JWT)
TOKEN=$(curl -s -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alvaro.diaz@alumnos.udg.mx","password":"Estudiante1!"}' \
  | jq -r .access_token)

# Horario con conflicto detectado automáticamente
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/v1/horarios/1 | jq '.bloques[] | select(.conflicto)'

# 44 salones con disponibilidad ahora calculada
curl http://localhost:5001/api/v1/salones | jq '.data[0]'

# Dashboard admin con KPIs
ADMIN=$(curl -s -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@udg.mx","password":"Admin1234!"}' | jq -r .access_token)
curl -H "Authorization: Bearer $ADMIN" \
  http://localhost:5001/api/v1/stats/dashboard | jq

# Export CSV de usuarios (descarga binaria)
curl -H "Authorization: Bearer $ADMIN" \
  http://localhost:5001/api/v1/stats/export/usuarios.csv -o usuarios.csv
```

---

## Estructura del repositorio

```
matute-guide/
├── README.md                  ← este archivo
├── MATUTE_GUIDE_PRD.md        ← spec completa (requisitos, modelos, endpoints)
├── seed.py                    ← población inicial reproducible
├── run.py                     ← entry point Flask (:5001)
├── config.py                  ← Desarrollo / Pruebas / Producción
├── requirements.txt
├── .env.example               ← variables sin secretos
├── app/
│   ├── __init__.py            ← create_app() factory
│   ├── extensions.py          ← db, migrate, jwt, cors, limiter
│   ├── api/                   ← 13 blueprints REST
│   ├── web/                   ← vistas Jinja
│   ├── models/                ← 19 modelos en 7 dominios
│   ├── utils/                 ← decorators, audit, notify, conflicts
│   ├── static/
│   │   ├── css/tokens.css     ← MapSchool v1 (cero hex hardcoded)
│   │   ├── css/style.css      ← componentes
│   │   └── js/app.js          ← Toast, Dialog, SSE, popover
│   └── templates/
│       ├── _base.html         ← layout + skip-link + aria-live
│       ├── components/        ← 27 macros + /components demo
│       ├── public/            ← landing, salones, mapa, oferta
│       ├── auth/              ← login, register, forgot, reset
│       ├── student/, profesor/, admin/
│       └── errors/
├── tests/                     ← pytest (15 tests)
├── flutter_app/               ← Android APK (Flutter 3.41)
│   ├── lib/
│   │   ├── main.dart
│   │   ├── theme/             ← MapColors + MapText (cero hex inline)
│   │   ├── services/          ← ApiService, AuthService, Storage, Notifications
│   │   ├── models/, providers/, widgets/, screens/  (21 pantallas)
│   ├── test/                  ← Dart unit + widget tests (43 tests)
│   ├── integration_test/      ← E2E test
│   ├── android/               ← keystore config + RELEASE.md
│   └── pubspec.yaml
└── Untitled Diagram.drawio · mapas.drawio   ← diagramas originales
```

---

## Roadmap inmediato

Cosas que todavía valen la pena agregar:

- [ ] Export PDF de reportes (CSV ya existe)
- [ ] Drag-and-drop real del plan de estudios admin (hoy son botones ← →)
- [ ] Migración a PostgreSQL en producción (modelos ya neutrales — sin SQL específico)
- [ ] CI/CD GitHub Actions: `pytest` + `flutter test` + build APK en cada PR
- [ ] Firma release del APK con keystore propio (ver `flutter_app/RELEASE.md`)
- [ ] Backups automáticos del audit log

---

## Documentación adicional

- **[`MATUTE_GUIDE_PRD.md`](./MATUTE_GUIDE_PRD.md)** — Especificación completa: 19 modelos con tipos, 13 blueprints con todos los endpoints, 21 componentes con specs CSS, 14 pantallas web con comportamiento, 13 pantallas Flutter, DoD por fase
- **[`flutter_app/RELEASE.md`](./flutter_app/RELEASE.md)** — Cómo generar keystore release, firmar APK/AAB, subir a Play Store
- **[`Untitled Diagram.drawio`](./Untitled%20Diagram.drawio)** y **[`mapas.drawio`](./mapas.drawio)** — Diagramas originales del proyecto

---

## Sistema de diseño

**MapSchool v1.0.0** — diseñado específicamente para Matute Guide:
- **Color**: navy `#172846` como primario, paleta navy 100→950, semánticos success/warning/danger/info
- **Tipografía**: Lexend (display) · DM Sans (body) · DM Mono (mono/badges)
- **Grid**: 4px baseline, escalas s-1 (4px) hasta s-20 (80px)
- **Componentes**: 27 piezas con variantes documentadas
- **Schedule blocks** color-coded por tipo: tronco común (navy-800) · área profesional (navy-500) · laboratorio (success) · idiomas (navy-400) · **conflicto (warning + borde danger pulsante)**
- **WCAG AA** en todos los pares texto/fondo (auditado)

---

## Licencia

MIT — uso libre para la red Universidad de Guadalajara y derivados.

---

*Hecho con foco en lo que la comunidad de CUValles realmente necesita.*
