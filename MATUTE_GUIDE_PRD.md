# Matute Guide — Product Requirements Document
## Versión 2.0 · Plataforma Escolar Completa

> **DESIGN SYSTEM:** MapSchool v1.0.0
> Tokens: navy `#172846`, Lexend (display), DM Sans (body), DM Mono (mono), 4px grid, WCAG AA.

---

## 0. VISIÓN Y ALCANCE

**Producto:** Matute Guide — Sistema de gestión escolar integral para la red Universidad de Guadalajara.
Reemplaza procesos manuales dispersos con una plataforma unificada: navegación del campus, horarios avanzados, calificaciones, asistencia, trámites, comunicaciones y administración académica completa.

**Stack:**
- Backend: Python 3.11 + Flask + SQLAlchemy + Flask-JWT-Extended + Flask-SocketIO
- Database: SQLite (dev) / PostgreSQL (prod)
- Web: Jinja2 + MapSchool CSS + Vanilla JS
- Mobile: Flutter 3.x → Android APK
- Notificaciones: SSE (web) + flutter_local_notifications (APK)

**Reglas absolutas:**
1. CERO datos hardcodeados. Todo viene de la BD vía API.
2. CERO colores hardcodeados. Todo usa tokens CSS o `MapColors` Flutter.
3. Todo el copy en español, segunda persona, acentos correctos.
4. WCAG AA en todos los pares texto/fondo.
5. Cada vista tiene su empty state.
6. Cada formulario tiene validación inline.
7. Soft-delete para entidades críticas (usuarios, horarios, materias).
8. Audit log para cada operación destructiva o privilegiada.

---

## 1. ROLES Y JERARQUÍA

```
RECTOR / DIRECTOR GENERAL
    └── DIRECTOR DE PLANTEL
            └── COORDINADOR ACADÉMICO
                    ├── PROFESOR
                    └── TUTOR
ADMINISTRADOR DEL SISTEMA  (rol técnico transversal)
ESTUDIANTE
ASPIRANTE                  (sin cuenta; acceso público)
INVITADO                   (cuenta limitada, sin carrera)
```

### Permisos por rol

| Acción | Rector | Director | Coordinador | Profesor | Admin | Estudiante |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Ver todas las escuelas | ✓ | — | — | — | ✓ | — |
| Gestionar usuarios | ✓ | ✓ plantel | ✓ dept. | — | ✓ | — |
| Publicar horarios | ✓ | ✓ | ✓ | — | ✓ | — |
| Capturar calificaciones | — | — | — | ✓ | ✓ | — |
| Solicitar trámites | — | — | — | — | — | ✓ |
| Ver analíticas | ✓ | ✓ plantel | ✓ dept. | — | ✓ | — |

---

## 2. MODELOS DE BASE DE DATOS

19 modelos SQLAlchemy organizados en 7 dominios:

### 2.1 Usuarios y Auth
- `Plantel` — Centro universitario
- `User` — Cuentas con rol, estado, soft-delete, expediente
- `RefreshToken` — JWT refresh con blacklist
- `AuditLog` — Registro inmutable de acciones privilegiadas

### 2.2 Estructura Académica
- `Carrera` — Programa con slug, duración, créditos, campos
- `Materia` — Clave, semestre, tipo (tronco_comun/area_profesional/laboratorio/idiomas), prerequisitos
- `PeriodoAcademico` — Semestre con apertura/cierre de inscripciones
- `CalendarioAcademico` — Eventos del periodo

### 2.3 Salones y Edificios
- `Edificio` — Coordenadas para mapa SVG
- `Salon` — Tipo, capacidad, equipamiento, posición
- `PuntoInteres` — Cafeterías, biblioteca, etc.

### 2.4 Sistema de Horarios
- `Horario` — Estado (borrador/en_revision/publicado/archivado), totales calculados
- `Bloque` — Día, hora, materia, salón, profesor, conflicto
- `PlantillaHorario` — Horario sugerido por carrera/semestre

### 2.5 Calificaciones y Asistencia
- `Inscripcion` — Estudiante ↔ materia en un periodo
- `Calificacion` — Por tipo (parcial_1, parcial_2, parcial_3, ordinario, extraordinario, final)
- `RegistroAsistencia` — Por bloque y fecha

### 2.6 Trámites
- `TipoTramite` — Catálogo
- `Tramite` — Folio TRM-YEAR-NNNNN, estado, documentos
- `SeguimientoTramite` — Timeline de cambios

### 2.7 Notificaciones
- `Notificacion` — Por usuario, con tipo y acción_url
- `Anuncio` — Para audiencias, fijable

---

## 3. API ENDPOINTS

Base URL: `/api/v1`. Auth: `Authorization: Bearer <access_token>`.

### Convenciones
- Paginación: `?page=1&per_page=25` → `{ data, total, page, pages }`
- Errores: `{ error: "mensaje", code: "CODE", field?: "campo" }`
- Timestamps: ISO 8601 UTC

### 3.1 AUTH — `/auth`
- `POST /auth/login` · `POST /auth/register` · `POST /auth/refresh` (con rotación)
- `POST /auth/logout` · `POST /auth/logout-all` · `GET /auth/me`
- `POST /auth/password/change` · `POST /auth/password/reset-request` · `POST /auth/password/reset`

### 3.2 USUARIOS — `/api/v1/users`
- `GET /` (paginado + filtros) · `GET /:id` · `POST /` · `PUT /:id` · `DELETE /:id` (soft)
- `POST /:id/suspender` · `POST /:id/restablecer`
- `GET /:id/horarios` · `GET /:id/tramites` · `GET /:id/calificaciones`

### 3.3 ACADÉMICO — `/api/v1`
- `GET/PUT /planteles` · `GET /planteles/:id/stats`
- `GET/POST/PUT/DELETE /carreras` · `GET /carreras/:id` (con plan_estudios)
- `GET/POST/PUT/DELETE /materias`
- `GET/POST/PUT /periodos` · `POST /periodos/:id/activar` · `GET/POST /periodos/:id/calendario`

### 3.4 CAMPUS — `/api/v1`
- `GET/POST/PUT/DELETE /edificios` · `GET /edificios/:id` (con salones)
- `GET/POST/PUT/DELETE /salones` · `GET /salones/:id` (con disponibilidad semanal)
- `GET /salones/:id/disponibilidad` · `GET /salones/buscar`

### 3.5 HORARIOS — `/api/v1/horarios`
- `GET /` · `POST /` · `GET /:id` · `PUT /:id` · `DELETE /:id`
- `POST /:id/publicar` · `POST /:id/clonar` · `GET /:id/exportar`
- `POST/PUT/DELETE /:id/bloques[/:bid]` (con detección de conflictos)
- Admin: `GET /admin` · `GET /admin/vista-{carrera,salon,profesor}`
- Plantillas: `GET/POST /plantillas` · `POST /:id/aplicar-plantilla`

### 3.6 INSCRIPCIONES — `/api/v1/inscripciones`
- `GET /` · `POST /` · `DELETE /:id` (baja)
- `GET/PUT /:id/calificaciones` · `POST /:id/calificaciones/publicar`
- `GET /:id/asistencia` · `POST /asistencia/masiva`

### 3.7 TRÁMITES — `/api/v1/tramites`
- `GET /tipos` · `GET /` · `POST /` (genera folio) · `GET /:id` · `PUT /:id/estado`

### 3.8 NOTIFICACIONES — `/api/v1/notificaciones`
- `GET /` · `POST /:id/leer` · `POST /leer-todas`
- `GET /stream` (SSE)

### 3.9 ANUNCIOS — `/api/v1/anuncios`
- `GET /` · `POST /` · `PUT /:id` · `DELETE /:id`

### 3.10 STATS — `/api/v1/stats`
- `GET /dashboard` · `GET /dashboard/publico`
- `GET /usuarios` · `GET /salones` · `GET /carreras`
- `GET /asistencia` · `GET /calificaciones`

### 3.11 MAPA — `/api/v1/mapa`
- `GET /` (edificios + POIs) · `GET /ruta` · `GET /buscar`

### 3.12 BÚSQUEDA — `/api/v1/buscar`
- `GET ?q=&tipos=usuarios,materias,salones,tramites`

### 3.13 AUDIT — `/api/v1/audit`
- `GET /` (filtros: user, accion, entidad, desde/hasta)

---

## 4. PÁGINAS WEB

### 4.1 Públicas (sin autenticación)
- `/` Landing con hero + features + stats reales + carreras preview
- `/auth/login` — Split layout, JWT + sesión Flask
- `/auth/register` — 3 pasos: datos personales / perfil / confirmación
- `/oferta` — Grid de carreras con plan de estudios
- `/oferta/:slug` — Detalle con materias por semestre
- `/salones` — Directorio con filtros + disponibilidad en tiempo real (60s)
- `/salones/:codigo` — Grilla semanal de disponibilidad
- `/mapa` — SVG interactivo con edificios + POIs

### 4.2 Portal Estudiante (rol=estudiante)
- `/dashboard` — 5 tabs: Resumen / Horario / Calificaciones / Asistencia / Trámites
- `/horario` — Constructor con quick-add, conflictos en tiempo real, publicar
- `/tramites` — Lista + crear (modal)
- `/perfil` — Editar datos + cambio de contraseña

### 4.3 Portal Profesor (rol=profesor)
- `/profesor` — Dashboard con grupos
- `/profesor/horario` — Horario asignado
- `/profesor/grupos/:id` — Lista de estudiantes + captura

### 4.4 Panel Administrativo (rol=admin|director|coordinador|rector)
- `/admin` — KPIs (estudiantes, horarios, conflictos, asistencia, trámites)
- `/admin/usuarios`, `/admin/estudiantes`, `/admin/profesores` — CRUD + bulk
- `/admin/horarios` — 3 vistas (carrera/edificio/profesor)
- `/admin/salones` — Cards/tabla agrupadas por edificio + CRUD
- `/admin/carreras`, `/admin/materias`, `/admin/periodos`
- `/admin/tramites` — Tabs por estado + cambio de estado
- `/admin/anuncios` — CRUD con preview
- `/admin/reportes` — Gráficas + export
- `/admin/audit` — Log inmutable
- `/admin/configuracion` — Plantel + tipos de trámite

### 4.5 `/components` — Demo interna (DEBUG=true)
21 secciones: colores, tipografía, botones, inputs, form controls, badges, avatars, tabs, alerts, toasts, dialogs, dropdown, tooltip, breadcrumbs, pagination, cards, stat cards, data table, empty states, schedule grid, notificaciones.

---

## 5. SCHEDULE GRID — ESPECIFICACIÓN

```css
.bloque-tronco-comun     { background: var(--navy-800); color: white; }
.bloque-area-profesional { background: var(--navy-500); color: white; }
.bloque-laboratorio      { background: var(--success);  color: white; }
.bloque-idiomas          { background: var(--navy-400); color: var(--ink-900); }
.bloque-conflicto        { background: var(--warning);  border: 2px solid var(--danger); }
```

Click en bloque → popover con materia, salón, profesor, hora, acciones.
Click en celda vacía → quick-add panel.

**Leyenda obligatoria** bajo el grid:
```
■ Tronco común  ■ Área profesional  ■ Laboratorio  ■ Idiomas  ■ Conflicto
```

---

## 6. NOTIFICACIONES — IMPLEMENTACIÓN

### Backend SSE
```python
@app.route('/api/v1/notificaciones/stream')
def notification_stream():
    user_id = get_jwt_identity()  # token vía query string
    def generate():
        last_check = datetime.utcnow()
        while True:
            time.sleep(10)
            nuevas = Notificacion.query.filter(
                destinatario_id=user_id,
                leida=False,
                created_at > last_check).all()
            for n in nuevas:
                yield f"data: {json.dumps(n.to_dict())}\n\n"
            last_check = datetime.utcnow()
    return Response(generate(), mimetype='text/event-stream')
```

### Frontend (EventSource)
```javascript
const evtSource = new EventSource('/api/v1/notificaciones/stream?token=' + jwt);
evtSource.onmessage = (e) => {
  const notif = JSON.parse(e.data);
  showToast(notif.titulo, notif.tipo);
  updateBellBadge();
};
```

---

## 7. MAPA DEL CAMPUS — SVG

SVG embedded en página, viewBox 1200×800. Edificios como `<g class="edificio">` con click handler que carga salones.

---

## 8. FLUTTER APK

### 8.1 Estructura
```
flutter_app/lib/
├── main.dart                ← MaterialApp.router + GoRouter
├── config/api_config.dart   ← baseUrl (10.0.2.2 emulador)
├── theme/                   ← MapColors + MapText + buildTheme()
├── services/                ← ApiService, AuthService, NotificationService, StorageService
├── models/                  ← User, Horario, Bloque, Salon, SalonDetail
├── providers/               ← AuthProvider (ChangeNotifier)
├── widgets/                 ← AppAvatar, StatusBadge, StatCard, ScheduleGrid
└── screens/
    ├── auth/                ← LoginScreen, RegisterScreen
    ├── student/             ← Dashboard (BottomNav 5), Horario, SalonesList,
    │                          Calificaciones, Asistencia, Tramites, Perfil
    ├── salones/             ← SalonDetailScreen
    ├── mapa/                ← MapaScreen (InteractiveViewer)
    ├── admin/               ← AdminDashboard (Drawer), Usuarios, Horarios, Salones
    ├── profesor/            ← ProfesorDashboard
    └── shared/              ← NotificacionesScreen
```

### 8.2 pubspec.yaml
```yaml
dependencies:
  flutter: { sdk: flutter }
  http: ^1.2.0
  provider: ^6.1.2
  shared_preferences: ^2.2.3
  google_fonts: ^6.2.1
  intl: ^0.19.0
  go_router: ^13.2.0
  flutter_svg: ^2.0.10+1
  fl_chart: ^0.68.0
  flutter_local_notifications: ^17.2.1+2
```

### 8.3 Auth flow
- `AuthService.login()` → `ApiService.post('/auth/login')` → guarda tokens en SharedPreferences
- `ApiService` interceptor: 401 → POST `/auth/refresh` → retry → si falla, `clear()` y emite logout
- GoRouter `redirect`: si `!loggedIn && !isAuthRoute` → `/login`

### 8.4 Reglas Flutter
- Cero `Color(0xFF…)` inline; siempre `MapColors.*`
- Cero `TextStyle(...)` inline; siempre `MapText.*` o helper
- `CircularProgressIndicator` color `MapColors.navy800`
- Notificaciones: polling cada 30s + `flutter_local_notifications`

---

## 9. SEED DATA

Mínimo:
- 1 plantel (CUValles)
- 3 carreras (Informática, Biotecnología, Energías Alternas)
- 5 edificios con 44 salones totales
- 72 materias (4 semestres × ~6 materias × 3 carreras)
- 1 periodo activo (2026-A)
- 12 usuarios: 1 admin, 1 director, 1 coordinador, 6 profesores, 3 estudiantes
- 1 horario completo del estudiante Álvaro CON conflicto real Mié 11:00 (Programación Web LAB-4 ↔ Bases de Datos II LAB-2)
- 5 tipos de trámite + 2 trámites de muestra con seguimiento
- Calificaciones publicadas + asistencia de 4 semanas
- 2 anuncios + 3 notificaciones para Álvaro

---

## 10. MEJORES PRÁCTICAS TÉCNICAS

### Flask
- Application Factory pattern (`create_app()`)
- Blueprints por dominio
- `flask-migrate` para migraciones (no `db.create_all()` en prod)
- Rate limiting en `/auth/login` (5–10 req/min)
- CORS explícito (no `*` en prod)
- Health check `GET /health`

### SQLAlchemy
- `lazy='select'` por defecto
- Índices en `user.email`, `notificacion.destinatario_id+leida`, `bloque.horario_id`
- `db.session.rollback()` en todos los `except`

### Seguridad
- bcrypt cost factor 12
- JWT access 1h, refresh 30d con rotación
- Blacklist de JTI revocados
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`

### CSS
- Solo `var(--token)` — cero hex hardcoded
- BEM light: `.componente__elemento--modificador`
- Mobile-first: breakpoints 768px tablet / 1024px desktop
- Focus visible 3px navy outline
- `prefers-reduced-motion` respetado

### Flutter
- Provider para auth + notificaciones
- GoRouter con auth guard
- Todos los colores: `MapColors.*`
- Todos los textos: `MapText.*`

---

## 11. DEFINITION OF DONE (DoD)

### Fase 1 — Backend ✓
- [x] `flask run` sin errores
- [x] `python seed.py` puebla la BD
- [x] `GET /health` retorna `{"status": "ok"}`
- [x] Endpoints auth funcionan (curl-testable)
- [x] JWT requerido → 401 sin token
- [x] Rol incorrecto → 403
- [x] Soft-delete funciona
- [x] Conflicto de bloque detectado
- [x] AuditLog en user.delete, user.suspend, horario.publish
- [x] Rate limiting en `/auth/login`
- [x] CORS configurado

### Fase 2 — Web ✓
- [x] `/components` muestra los 21 componentes
- [x] CERO colores hardcodeados
- [x] Páginas públicas accesibles sin token
- [x] Login/logout/register end-to-end
- [x] Redirect según rol
- [x] Dashboard estudiante con datos reales
- [x] ScheduleGrid muestra conflicto Mié 11:00
- [x] SSE de notificaciones
- [x] Admin usuarios CRUD
- [x] Admin salones CRUD
- [x] Admin horarios 3 vistas
- [x] Mapa SVG interactivo
- [x] Trámites: crear → folio → notificación admin
- [x] Copy en español

### Fase 3 — Flutter APK ✓
- [x] `flutter build apk --release` compila
- [x] APK instala en Android 10+ (minSdk 21)
- [x] Login funciona vs Flask
- [x] HorarioScreen con colores correctos por tipo
- [x] Bloque conflicto: warning + label "CONFLICTO"
- [x] SalonesScreen agrupado
- [x] Notificaciones con flutter_local_notifications + polling 30s
- [x] 401 → refresh → retry → logout
- [x] AdminDashboard con KPIs
- [x] CERO `Color(0xFF...)` hardcoded
- [x] CERO `TextStyle(...)` inline

---

## 12. CUENTAS DE PRUEBA (seed.py)

| Email | Password | Rol |
|---|---|---|
| `admin@udg.mx` | `Admin1234!` | admin |
| `cristina.aguirre@udg.mx` | `Director1!` | director |
| `coordinador@udg.mx` | `Coordinador1!` | coordinador |
| `alvaro.diaz@alumnos.udg.mx` | `Estudiante1!` | estudiante (4° Informática, con conflicto Mié 11:00) |
| `yael.vega@alumnos.udg.mx` | `Estudiante1!` | estudiante (2° Biotecnología) |
| `rocio.castellanos@alumnos.udg.mx` | `Estudiante1!` | estudiante (6° Energías) |
| `jorge.mendez@udg.mx` | `Profesor1!` | profesor (Cálculo I) |
| `laura.lopez@udg.mx` | `Profesor1!` | profesor |
| `andrea.reyes@udg.mx` | `Profesor1!` | profesor |
| `patricia.torres@udg.mx` | `Profesor1!` | profesor |
| `roberto.brown@udg.mx` | `Profesor1!` | profesor (Inglés) |
| `estela.vargas@udg.mx` | `Profesor1!` | profesor |
