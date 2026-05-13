# Matute Guide — Product Requirements Document
## Versión 2.0 · Plataforma Escolar Completa
### Documento de referencia para Claude Code

---

> **DESIGN SYSTEM:** MapSchool v1.0.0
> URL: https://claude.ai/design/p/019e1eed-86d4-764b-8fe6-e93ca122fced?file=MapSchool+Design+System-print.html&via=share
> Tokens, componentes y patrones: navy `#172846`, Lexend (display), DM Sans (body), DM Mono (mono), 4px grid, WCAG AA.
> Claude Code DEBE leer y aplicar este design system en CADA componente web y Flutter.

---

## 0. VISIÓN Y ALCANCE

**Producto:** Matute Guide — Sistema de gestión escolar integral para la red Universidad de Guadalajara.
Reemplaza procesos manuales dispersos con una plataforma unificada: navegación del campus, horarios avanzados, calificaciones, asistencia, trámites, comunicaciones y administración académica completa.

**Repo:** `https://github.com/MapSchool1/web`
**Stack:**
- Backend: Python 3.11 + Flask + SQLAlchemy + Flask-JWT-Extended + Flask-SocketIO
- Database: PostgreSQL (SQLite para dev local; sin SQL engine-specific syntax)
- Web Frontend: Jinja2 + MapSchool CSS + Vanilla JS (sin framework pesado)
- Mobile: Flutter 3.x → Android APK (.apk release)
- Notificaciones: Server-Sent Events (SSE) + Firebase Cloud Messaging para push en APK
- Caché: Flask-Caching (simple in-memory en dev, Redis en prod)

**Reglas absolutas (no negociables):**
1. CERO datos hardcodeados. Todo viene de la BD vía API.
2. CERO colores hardcodeados. Todo usa tokens CSS o `MapColors` Flutter.
3. Todo el copy en español, segunda persona, acentos correctos.
4. WCAG AA en todos los pares texto/fondo.
5. Cada vista tiene su empty state.
6. Cada formulario tiene validación inline.
7. Soft-delete para entidades críticas (usuarios, horarios, materias). NUNCA `DELETE`.
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
| Ver propio horario | — | — | — | ✓ | — | ✓ |
| Solicitar trámites | — | — | — | — | — | ✓ |
| Ver analíticas | ✓ | ✓ plantel | ✓ dept. | — | ✓ | — |
| Gestionar salones | ✓ | ✓ | ✓ | — | ✓ | — |
| Enviar anuncios | ✓ | ✓ | ✓ | ✓ | ✓ | — |

---

## 2. MODELOS DE BASE DE DATOS

### 2.1 Usuarios y Auth

```python
class Plantel(Base):
    """Centro universitario / escuela preparatoria"""
    id            = Column(Integer, PK)
    nombre        = Column(String(150), nullable=False)      # "CUValles", "CUCEI"
    clave         = Column(String(20), unique=True)           # "CUV", "CUCEI"
    ciudad        = Column(String(100))
    direccion     = Column(Text)
    activo        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=utcnow)

class User(Base):
    id            = Column(Integer, PK)
    email         = Column(String(120), unique=True, nullable=False, index=True)
    nombre        = Column(String(100), nullable=False)
    apellido_p    = Column(String(100), nullable=False)
    apellido_m    = Column(String(100))
    password_hash = Column(String(256), nullable=False)
    rol           = Column(Enum('rector','director','coordinador','profesor',
                                'admin','estudiante','invitado','aspirante'),
                           default='estudiante', nullable=False)
    estado        = Column(Enum('activo','suspendido','inactivo','eliminado'),
                           default='activo', nullable=False)
    plantel_id    = Column(Integer, FK('plantel.id'), nullable=True)
    expediente    = Column(String(30), unique=True, nullable=True)
    avatar_color  = Column(String(7), default='#172846')  # para iniciales
    telefono      = Column(String(20), nullable=True)
    semestre_actual = Column(Integer, nullable=True)      # solo estudiantes
    carrera_id    = Column(Integer, FK('carrera.id'), nullable=True)
    intentos_fallidos = Column(Integer, default=0)
    ultimo_acceso = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=utcnow)
    updated_at    = Column(DateTime, onupdate=utcnow)
    deleted_at    = Column(DateTime, nullable=True)  # soft-delete

class RefreshToken(Base):
    id            = Column(Integer, PK)
    user_id       = Column(Integer, FK('user.id'), nullable=False)
    token_jti     = Column(String(36), unique=True, nullable=False)  # JWT ID
    expires_at    = Column(DateTime, nullable=False)
    revoked       = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=utcnow)

class AuditLog(Base):
    """Registro inmutable de acciones privilegiadas"""
    id            = Column(Integer, PK)
    user_id       = Column(Integer, FK('user.id'))
    accion        = Column(String(100))    # 'user.delete', 'horario.publish'
    entidad       = Column(String(50))     # 'User', 'Horario'
    entidad_id    = Column(Integer)
    payload_antes = Column(JSON)           # estado antes
    payload_despues = Column(JSON)         # estado después
    ip            = Column(String(45))
    user_agent    = Column(String(255))
    created_at    = Column(DateTime, default=utcnow)
```

### 2.2 Estructura Académica

```python
class Carrera(Base):
    id            = Column(Integer, PK)
    nombre        = Column(String(200), nullable=False)
    nombre_corto  = Column(String(50))               # "Tec. Informática"
    slug          = Column(String(100), unique=True)
    descripcion   = Column(Text)
    duracion_semestres = Column(Integer, default=8)
    creditos_totales   = Column(Integer, default=300)
    campos        = Column(String(255))              # "desarrollo, soporte, redes"
    plantel_id    = Column(Integer, FK('plantel.id'))
    activa        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=utcnow)
    updated_at    = Column(DateTime, onupdate=utcnow)

class Materia(Base):
    id            = Column(Integer, PK)
    clave         = Column(String(20), unique=True)  # "INF-301"
    nombre        = Column(String(200), nullable=False)
    nombre_corto  = Column(String(80))
    carrera_id    = Column(Integer, FK('carrera.id'), nullable=False)
    semestre      = Column(Integer, nullable=False)   # 1–8
    tipo          = Column(Enum('tronco_comun','area_profesional',
                                'laboratorio','idiomas'), nullable=False)
    creditos      = Column(Integer, default=6)
    horas_teoria  = Column(Integer, default=2)
    horas_practica = Column(Integer, default=2)
    prerequisitos = Column(JSON)                     # [materia_id, ...]
    activa        = Column(Boolean, default=True)

class PeriodoAcademico(Base):
    """Semestre/cuatrimestre escolar"""
    id            = Column(Integer, PK)
    clave         = Column(String(20), unique=True)   # "2026-A", "2026-B"
    nombre        = Column(String(100))               # "Primavera 2026"
    plantel_id    = Column(Integer, FK('plantel.id'))
    fecha_inicio  = Column(Date, nullable=False)
    fecha_fin     = Column(Date, nullable=False)
    apertura_inscripciones  = Column(DateTime)
    cierre_inscripciones    = Column(DateTime)
    activo        = Column(Boolean, default=False)    # solo 1 activo por plantel
    created_at    = Column(DateTime, default=utcnow)

class CalendarioAcademico(Base):
    """Eventos del calendario escolar"""
    id            = Column(Integer, PK)
    periodo_id    = Column(Integer, FK('periodo_academico.id'))
    titulo        = Column(String(200))
    descripcion   = Column(Text)
    tipo          = Column(Enum('examen','vacaciones','evento',
                                'feriado','entrega','otro'))
    fecha_inicio  = Column(Date)
    fecha_fin     = Column(Date)
    aplica_a      = Column(Enum('todos','estudiantes','profesores','admin'))
    color         = Column(String(7))  # token de color
```

### 2.3 Salones y Edificios

```python
class Edificio(Base):
    id            = Column(Integer, PK)
    plantel_id    = Column(Integer, FK('plantel.id'))
    nombre        = Column(String(100))    # "Edificio A"
    clave         = Column(String(10), unique=True)   # "A"
    descripcion   = Column(Text)
    coordenadas_x = Column(Float)          # para mapa SVG
    coordenadas_y = Column(Float)
    ancho_mapa    = Column(Float)          # dimensiones en mapa
    alto_mapa     = Column(Float)
    color_mapa    = Column(String(7), default='#172846')
    activo        = Column(Boolean, default=True)

class Salon(Base):
    id            = Column(Integer, PK)
    edificio_id   = Column(Integer, FK('edificio.id'), nullable=False)
    codigo        = Column(String(20), unique=True, nullable=False)  # "A-203"
    nombre        = Column(String(100))                # "Aula Magna", "Lab Redes"
    tipo          = Column(Enum('aula','laboratorio','auditorio',
                                'sala_computo','sala_idiomas','otro'))
    capacidad     = Column(Integer, nullable=False)
    piso          = Column(Integer, default=1)
    descripcion   = Column(Text)
    equipamiento  = Column(JSON)           # ["proyector","AC","pizarron_digital"]
    coord_x       = Column(Float)          # posición en planta del edificio
    coord_y       = Column(Float)
    activo        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=utcnow)
    updated_at    = Column(DateTime, onupdate=utcnow)
```

### 2.4 Sistema de Horarios (Avanzado)

```python
class Horario(Base):
    id            = Column(Integer, PK)
    user_id       = Column(Integer, FK('user.id'), nullable=False)
    periodo_id    = Column(Integer, FK('periodo_academico.id'), nullable=False)
    nombre        = Column(String(100))
    estado        = Column(Enum('borrador','en_revision','publicado','archivado'),
                           default='borrador')
    total_creditos = Column(Integer, default=0)   # calculado
    total_horas   = Column(Integer, default=0)    # calculado
    tiene_conflictos = Column(Boolean, default=False)  # calculado
    publicado_at  = Column(DateTime)
    created_at    = Column(DateTime, default=utcnow)
    updated_at    = Column(DateTime, onupdate=utcnow)
    deleted_at    = Column(DateTime, nullable=True)

class Bloque(Base):
    id            = Column(Integer, PK)
    horario_id    = Column(Integer, FK('horario.id'), nullable=False)
    materia_id    = Column(Integer, FK('materia.id'), nullable=False)
    salon_id      = Column(Integer, FK('salon.id'), nullable=True)
    profesor_id   = Column(Integer, FK('user.id'), nullable=True)
    dia           = Column(Enum('lun','mar','mie','jue','vie','sab'),
                           nullable=False)
    hora_inicio   = Column(Time, nullable=False)   # 07:00
    hora_fin      = Column(Time, nullable=False)   # 09:00
    tipo_sesion   = Column(Enum('teoria','practica','laboratorio','examen'))
    conflicto     = Column(Boolean, default=False)
    conflicto_con = Column(JSON)   # [bloque_id, ...] de bloques en conflicto
    notas         = Column(Text)

class PlantillaHorario(Base):
    """Horario base sugerido para una carrera/semestre"""
    id            = Column(Integer, PK)
    carrera_id    = Column(Integer, FK('carrera.id'))
    semestre      = Column(Integer)
    periodo_id    = Column(Integer, FK('periodo_academico.id'))
    nombre        = Column(String(100))
    bloques       = Column(JSON)   # [{materia_id, dia, hora_inicio, hora_fin}, ...]
    activa        = Column(Boolean, default=True)
    created_by    = Column(Integer, FK('user.id'))
    created_at    = Column(DateTime, default=utcnow)
```

### 2.5 Calificaciones y Asistencia

```python
class Inscripcion(Base):
    """Relación estudiante ↔ materia en un periodo"""
    id            = Column(Integer, PK)
    estudiante_id = Column(Integer, FK('user.id'), nullable=False)
    materia_id    = Column(Integer, FK('materia.id'), nullable=False)
    periodo_id    = Column(Integer, FK('periodo_academico.id'), nullable=False)
    grupo         = Column(String(10))     # "A", "B", "LAB-1"
    profesor_id   = Column(Integer, FK('user.id'))
    estado        = Column(Enum('activa','baja','baja_justificada','aprobada',
                                'reprobada'), default='activa')
    created_at    = Column(DateTime, default=utcnow)

class Calificacion(Base):
    id            = Column(Integer, PK)
    inscripcion_id = Column(Integer, FK('inscripcion.id'), nullable=False)
    tipo          = Column(Enum('parcial_1','parcial_2','parcial_3',
                                'ordinario','extraordinario','final'))
    valor         = Column(Numeric(4, 2))    # 0.00 – 10.00
    observaciones = Column(Text)
    capturado_por = Column(Integer, FK('user.id'))
    capturado_at  = Column(DateTime, default=utcnow)
    publicado     = Column(Boolean, default=False)
    publicado_at  = Column(DateTime)

class RegistroAsistencia(Base):
    id            = Column(Integer, PK)
    inscripcion_id = Column(Integer, FK('inscripcion.id'), nullable=False)
    bloque_id     = Column(Integer, FK('bloque.id'), nullable=False)
    fecha         = Column(Date, nullable=False)
    estado        = Column(Enum('presente','ausente','justificado','retardo'))
    justificacion = Column(Text)
    registrado_por = Column(Integer, FK('user.id'))
    created_at    = Column(DateTime, default=utcnow)
```

### 2.6 Trámites Administrativos

```python
class TipoTramite(Base):
    id            = Column(Integer, PK)
    nombre        = Column(String(150))    # "Constancia de estudios"
    descripcion   = Column(Text)
    requiere_documentos = Column(JSON)     # ["acta", "ine", ...]
    costo         = Column(Numeric(10,2), default=0)
    tiempo_estimado_dias = Column(Integer, default=3)
    activo        = Column(Boolean, default=True)

class Tramite(Base):
    id            = Column(Integer, PK)
    folio         = Column(String(20), unique=True)   # "TRM-2026-00142"
    solicitante_id = Column(Integer, FK('user.id'), nullable=False)
    tipo_tramite_id = Column(Integer, FK('tipo_tramite.id'), nullable=False)
    estado        = Column(Enum('recibido','en_proceso','pendiente_pago',
                                'listo','entregado','rechazado'), default='recibido')
    descripcion   = Column(Text)
    documentos    = Column(JSON)                      # paths a archivos
    resultado_url = Column(String(500))               # link al documento generado
    atendido_por  = Column(Integer, FK('user.id'))
    notas_admin   = Column(Text)
    created_at    = Column(DateTime, default=utcnow)
    updated_at    = Column(DateTime, onupdate=utcnow)
    entregado_at  = Column(DateTime)

class SeguimientoTramite(Base):
    id            = Column(Integer, PK)
    tramite_id    = Column(Integer, FK('tramite.id'))
    estado_anterior = Column(String(30))
    estado_nuevo  = Column(String(30))
    comentario    = Column(Text)
    usuario_id    = Column(Integer, FK('user.id'))
    created_at    = Column(DateTime, default=utcnow)
```

### 2.7 Notificaciones y Comunicación

```python
class Notificacion(Base):
    id            = Column(Integer, PK)
    destinatario_id = Column(Integer, FK('user.id'), nullable=False, index=True)
    tipo          = Column(Enum('horario','calificacion','tramite','anuncio',
                                'sistema','conflicto','asistencia'))
    titulo        = Column(String(200))
    cuerpo        = Column(Text)
    leida         = Column(Boolean, default=False, index=True)
    accion_url    = Column(String(500))   # deep link relativo
    metadata      = Column(JSON)          # datos extra para el cliente
    created_at    = Column(DateTime, default=utcnow)
    leida_at      = Column(DateTime)

class Anuncio(Base):
    id            = Column(Integer, PK)
    autor_id      = Column(Integer, FK('user.id'))
    plantel_id    = Column(Integer, FK('plantel.id'))
    titulo        = Column(String(200))
    cuerpo        = Column(Text)
    audiencia     = Column(Enum('todos','estudiantes','profesores','admin'))
    carrera_id    = Column(Integer, FK('carrera.id'), nullable=True)  # null = todos
    fijado        = Column(Boolean, default=False)
    publicado     = Column(Boolean, default=False)
    publicado_at  = Column(DateTime)
    expira_at     = Column(DateTime)
    created_at    = Column(DateTime, default=utcnow)
```

### 2.8 Mapa del Campus

```python
class PuntoInteres(Base):
    id            = Column(Integer, PK)
    plantel_id    = Column(Integer, FK('plantel.id'))
    nombre        = Column(String(100))
    tipo          = Column(Enum('edificio','bano','cafeteria','biblioteca',
                                'enfermeria','estacionamiento','canchas','otro'))
    descripcion   = Column(Text)
    coord_x       = Column(Float)
    coord_y       = Column(Float)
    icono         = Column(String(50))   # nombre del icono del sistema
    activo        = Column(Boolean, default=True)
```

---

## 3. API ENDPOINTS COMPLETOS

### Convenciones
- Base URL: `/api/v1`
- Autenticación: `Authorization: Bearer <access_token>`
- Paginación: `?page=1&per_page=25` → `{ data, total, page, pages, per_page }`
- Errores: `{ error: "mensaje", code: "ERROR_CODE", field?: "campo" }`
- Timestamps: ISO 8601 UTC

---

### 3.1 AUTH — `/auth`

```
POST   /auth/login
  body: { email, password }
  returns: { access_token, refresh_token, expires_in: 3600, user: UserDTO }
  errors: 401 credenciales, 403 cuenta suspendida/eliminada

POST   /auth/register
  body: { nombre, apellido_p, apellido_m?, email, password, rol?, plantel_id? }
  returns: { access_token, refresh_token, user: UserDTO }
  errors: 409 email duplicado, 422 validación

POST   /auth/refresh
  body: { refresh_token }
  returns: { access_token, expires_in }
  errors: 401 token inválido/expirado/revocado

POST   /auth/logout           [JWT]
  body: { refresh_token }
  acción: revoca refresh_token en BD
  returns: { message: "Sesión cerrada" }

POST   /auth/logout-all       [JWT]
  acción: revoca TODOS los refresh_tokens del user
  returns: { message: "Todas las sesiones cerradas" }

GET    /auth/me               [JWT]
  returns: { user: UserDTO }

POST   /auth/password/change  [JWT]
  body: { password_actual, password_nuevo }
  returns: { message: "Contraseña actualizada" }

POST   /auth/password/reset-request
  body: { email }
  acción: genera token, envía email (o lo imprime en dev)
  returns: { message: "Correo enviado si existe la cuenta" }

POST   /auth/password/reset
  body: { token, password_nuevo }
  returns: { message: "Contraseña restablecida" }
```

### 3.2 USUARIOS — `/api/v1/users`

```
GET    /api/v1/users          [JWT + admin|director|coordinador]
  query: ?search=&rol=&estado=&plantel_id=&carrera_id=&page=&per_page=
  returns: { data: [UserDTO], total, page, pages }

GET    /api/v1/users/:id      [JWT + admin|propio]
  returns: { user: UserDTO, estadisticas: { horarios, tramites, asistencia_prom } }

POST   /api/v1/users          [JWT + admin]
  body: { nombre, apellido_p, email, rol, plantel_id, carrera_id?, password_temporal }
  returns: { user: UserDTO }

PUT    /api/v1/users/:id      [JWT + admin|propio con límites]
  body: campos parciales — admin puede cambiar rol/estado, user solo datos personales
  returns: { user: UserDTO }

DELETE /api/v1/users/:id      [JWT + admin]
  acción: soft-delete → deleted_at=now, estado=eliminado
  audit log requerido
  returns: { message: "Usuario eliminado" }

POST   /api/v1/users/:id/suspender    [JWT + admin|director]
  body: { motivo }
  returns: { user: UserDTO }

POST   /api/v1/users/:id/restablecer  [JWT + admin]
  acción: estado=activo, intentos_fallidos=0
  returns: { user: UserDTO }

GET    /api/v1/users/:id/horarios     [JWT + admin|propio]
  returns: { horarios: [HorarioDTO] }

GET    /api/v1/users/:id/tramites     [JWT + admin|propio]
  returns: { tramites: [TramiteDTO] }

GET    /api/v1/users/:id/calificaciones  [JWT + admin|propio|profesor]
  returns: { inscripciones: [{ materia, calificaciones, asistencia_pct }] }
```

**UserDTO:**
```json
{
  "id": 1,
  "nombre": "Álvaro",
  "apellido_p": "Díaz",
  "apellido_m": "Ramírez",
  "nombre_completo": "Álvaro Díaz Ramírez",
  "iniciales": "AD",
  "email": "alvaro.diaz@alumnos.udg.mx",
  "rol": "estudiante",
  "estado": "activo",
  "expediente": "218 492",
  "avatar_color": "#172846",
  "plantel": { "id": 1, "nombre": "CUValles", "clave": "CUV" },
  "carrera": { "id": 2, "nombre": "Tec. en Informática", "slug": "tec-informatica" },
  "semestre_actual": 4,
  "ultimo_acceso": "2026-05-12T09:23:00Z",
  "created_at": "2025-08-01T10:00:00Z"
}
```

### 3.3 PLANTELES — `/api/v1/planteles`

```
GET    /api/v1/planteles                [público]
PUT    /api/v1/planteles/:id            [JWT + rector|admin]
GET    /api/v1/planteles/:id/stats      [JWT + director|admin]
```

### 3.4 CARRERAS — `/api/v1/carreras`

```
GET    /api/v1/carreras                 [público]
  query: ?plantel_id=&activa=true
  returns: { data: [CarreraDTO] }

GET    /api/v1/carreras/:id             [público]
  returns: { carrera: CarreraDTO, plan_estudios: { "1": [Materia], ..., "8": [Materia] } }

POST   /api/v1/carreras                 [JWT + coordinador|admin]
PUT    /api/v1/carreras/:id             [JWT + coordinador|admin]
DELETE /api/v1/carreras/:id             [JWT + director|admin]  soft
```

### 3.5 MATERIAS — `/api/v1/materias`

```
GET    /api/v1/materias                 [JWT]
  query: ?carrera_id=&semestre=&tipo=&activa=true
  returns: { data: [MateriaDTO] }

GET    /api/v1/materias/:id             [JWT]
  returns: { materia, inscripciones_periodo_actual: N }

POST   /api/v1/materias                 [JWT + coordinador|admin]
PUT    /api/v1/materias/:id             [JWT + coordinador|admin]
DELETE /api/v1/materias/:id             [JWT + coordinador|admin]  soft
```

### 3.6 PERIODOS ACADÉMICOS — `/api/v1/periodos`

```
GET    /api/v1/periodos                 [público]
GET    /api/v1/periodos/activo          [público]  → periodo activo del plantel
POST   /api/v1/periodos                 [JWT + director|admin]
PUT    /api/v1/periodos/:id             [JWT + director|admin]
POST   /api/v1/periodos/:id/activar     [JWT + director|admin]
  acción: desactiva el anterior, activa este
GET    /api/v1/periodos/:id/calendario  [JWT]
  returns: { eventos: [CalendarioDTO] }
POST   /api/v1/periodos/:id/calendario  [JWT + coordinador|admin]
```

### 3.7 EDIFICIOS — `/api/v1/edificios`

```
GET    /api/v1/edificios                [público]
  query: ?plantel_id=
  returns: { data: [EdificioDTO con total_salones] }

GET    /api/v1/edificios/:id            [público]
  returns: { edificio, salones: [SalonDTO] }

GET    /api/v1/edificios/:id/mapa       [público]
  returns: { svg_data: "...", puntos: [PuntoInteres] }

POST/PUT/DELETE /api/v1/edificios       [JWT + admin]
```

### 3.8 SALONES — `/api/v1/salones`

```
GET    /api/v1/salones                  [público]
  query: ?edificio_id=&tipo=&capacidad_min=&activo=true&disponible_ahora=true
  returns: { data: [SalonDTO con disponible_ahora calculado] }

GET    /api/v1/salones/:id              [público]
  returns: {
    salon: SalonDTO,
    disponibilidad_semana: {
      "lun": [{ hora_inicio, hora_fin, ocupado, materia?, grupo? }],
      "mar": [...], ...
    },
    proximos_libres: [{ dia, hora_inicio, hora_fin }]
  }

GET    /api/v1/salones/:id/disponibilidad  [público]
  query: ?dia=lun&hora_inicio=09:00&hora_fin=11:00&periodo_id=
  returns: { disponible: bool, conflictos: [...] }

GET    /api/v1/salones/buscar           [JWT]
  query: ?dia=lun&hora_inicio=09:00&hora_fin=11:00&tipo=&capacidad_min=
  returns: { disponibles: [SalonDTO], ocupados: [SalonDTO] }

POST   /api/v1/salones                  [JWT + coordinador|admin]
  body: { edificio_id, codigo, nombre?, tipo, capacidad, piso, equipamiento, coord_x?, coord_y? }

PUT    /api/v1/salones/:id              [JWT + coordinador|admin]
DELETE /api/v1/salones/:id              [JWT + admin]  soft (activo=False)
```

### 3.9 HORARIOS — `/api/v1/horarios`

```
GET    /api/v1/horarios                 [JWT — propios del user]
  query: ?periodo_id=&estado=
  returns: { data: [HorarioDTO] }

POST   /api/v1/horarios                 [JWT — estudiante]
  body: { periodo_id, nombre? }
  validación: no puede haber más de 1 horario activo por periodo
  returns: { horario: HorarioDTO }

GET    /api/v1/horarios/:id             [JWT — dueño|admin|coordinador]
  returns: {
    horario: HorarioDTO,
    bloques: [BloqueDTO con materia, salon, profesor expandidos],
    stats: { total_creditos, total_horas, materias_count, conflictos_count }
  }

PUT    /api/v1/horarios/:id             [JWT — dueño]
  body: { nombre?, estado? }
  si estado → 'publicado': valida que no tenga conflictos
  returns: { horario: HorarioDTO }

DELETE /api/v1/horarios/:id             [JWT — dueño]
  solo si estado='borrador'
  returns: { message }

POST   /api/v1/horarios/:id/publicar    [JWT — dueño|coordinador]
  validación: 0 conflictos, periodo abierto
  acción: estado='publicado', publicado_at=now
  notificación: al estudiante "Tu horario fue publicado"
  returns: { horario: HorarioDTO }

POST   /api/v1/horarios/:id/clonar      [JWT — dueño]
  acción: crea copia como borrador en mismo periodo
  returns: { horario: HorarioDTO nuevo }

GET    /api/v1/horarios/:id/exportar    [JWT — dueño|admin]
  query: ?formato=pdf|ical
  returns: archivo binario

# BLOQUES
POST   /api/v1/horarios/:id/bloques     [JWT — dueño]
  body: { materia_id, salon_id?, profesor_id?, dia, hora_inicio, hora_fin, tipo_sesion? }
  validación:
    - hora_inicio < hora_fin
    - no solapamiento con bloques existentes del MISMO horario
    - si salon_id: verificar disponibilidad del salon en ese bloque
    - marca conflicto=True si hay solapamiento, retorna 200 con advertencia (no 422)
  retorna: { bloque: BloqueDTO, conflictos: [BloqueDTO]?, advertencia?: "..." }

PUT    /api/v1/horarios/:id/bloques/:bid  [JWT — dueño]
DELETE /api/v1/horarios/:id/bloques/:bid  [JWT — dueño]

# HORARIOS ADMIN
GET    /api/v1/horarios/admin           [JWT + coordinador|admin]
  query: ?carrera_id=&periodo_id=&estado=&user_id=&page=&per_page=
  returns: { data: [HorarioDTO con user expandido], total, ... }

GET    /api/v1/horarios/admin/vista-carrera  [JWT + coordinador|admin]
  query: ?carrera_id=&semestre=&periodo_id=
  returns: { bloques_consolidados: [...], conflictos_globales: N }

GET    /api/v1/horarios/admin/vista-salon    [JWT + coordinador|admin]
  query: ?salon_id=&periodo_id=
  returns: { disponibilidad completa del salon }

GET    /api/v1/horarios/admin/vista-profesor  [JWT + coordinador|admin]
  query: ?profesor_id=&periodo_id=
  returns: { horario del profesor (bloques donde es asignado) }

# PLANTILLAS
GET    /api/v1/horarios/plantillas          [JWT + coordinador|admin]
POST   /api/v1/horarios/plantillas          [JWT + coordinador|admin]
POST   /api/v1/horarios/:id/aplicar-plantilla  [JWT — dueño]
  body: { plantilla_id }
  acción: crea bloques según plantilla, detecta conflictos
  returns: { bloques_creados: N, conflictos: N, bloques: [...] }
```

### 3.10 INSCRIPCIONES — `/api/v1/inscripciones`

```
GET    /api/v1/inscripciones            [JWT — propias]
  query: ?periodo_id=
  returns: { data: [InscripcionDTO con materia, profesor] }

POST   /api/v1/inscripciones            [JWT — estudiante|admin]
  body: { materia_id, periodo_id, grupo? }
  validación: periodo abierto, cupo disponible, sin prerequisitos pendientes
  returns: { inscripcion: InscripcionDTO }

DELETE /api/v1/inscripciones/:id        [JWT — estudiante durante periodo abierto]
  soft: estado='baja'
  returns: { message }

# CALIFICACIONES
GET    /api/v1/inscripciones/:id/calificaciones  [JWT — dueño|profesor|admin]
PUT    /api/v1/inscripciones/:id/calificaciones  [JWT + profesor]
  body: { tipo, valor, observaciones? }
  acción: crea/actualiza calificación, puede publicar=false
  returns: { calificacion: CalificacionDTO }

POST   /api/v1/inscripciones/:id/calificaciones/publicar  [JWT + coordinador|admin]

# ASISTENCIA
GET    /api/v1/inscripciones/:id/asistencia       [JWT — dueño|profesor|admin]
  returns: { registros: [...], porcentaje: 94.2, faltas: 3, justificadas: 1 }

POST   /api/v1/inscripciones/asistencia/masiva    [JWT + profesor]
  body: { bloque_id, fecha, registros: [{ inscripcion_id, estado, justificacion? }] }
  returns: { procesados: N }
```

### 3.11 TRÁMITES — `/api/v1/tramites`

```
GET    /api/v1/tramites/tipos           [público]
  returns: { data: [TipoTramiteDTO] }

GET    /api/v1/tramites                 [JWT — propios | admin: todos]
  query: ?estado=&tipo_id=&page=
  returns: { data: [TramiteDTO] }

POST   /api/v1/tramites                 [JWT — estudiante]
  body: { tipo_tramite_id, descripcion?, documentos?: [base64] }
  acción: genera folio TRM-YEAR-NNNNN, notifica al admin
  returns: { tramite: TramiteDTO }

GET    /api/v1/tramites/:id             [JWT — solicitante|admin]
  returns: { tramite: TramiteDTO, seguimiento: [SeguimientoDTO] }

PUT    /api/v1/tramites/:id/estado      [JWT + admin]
  body: { estado, comentario? }
  acción: actualiza, crea SeguimientoTramite, notifica al solicitante
  returns: { tramite: TramiteDTO }
```

### 3.12 NOTIFICACIONES — `/api/v1/notificaciones`

```
GET    /api/v1/notificaciones           [JWT]
  query: ?leida=false&tipo=&page=
  returns: { data: [NotificacionDTO], no_leidas: N }

POST   /api/v1/notificaciones/:id/leer  [JWT]
POST   /api/v1/notificaciones/leer-todas  [JWT]

# SSE endpoint para notificaciones en tiempo real
GET    /api/v1/notificaciones/stream    [JWT]
  Content-Type: text/event-stream
  Emite: data: { tipo, titulo, cuerpo, accion_url }

# ANUNCIOS
GET    /api/v1/anuncios                 [JWT]
  returns: { data: [AnuncioDTO], fijados: [AnuncioDTO] }

POST   /api/v1/anuncios                 [JWT + coordinador|admin]
PUT    /api/v1/anuncios/:id             [JWT + autor|admin]
DELETE /api/v1/anuncios/:id             [JWT + autor|admin]
```

### 3.13 ESTADÍSTICAS Y REPORTES — `/api/v1/stats`

```
GET    /api/v1/stats/dashboard          [JWT + admin|director]
  returns: {
    estudiantes_activos: { total: 14218, delta: 2.4, periodo: "vs sem. anterior" },
    horarios_publicados: { total: 86, meta: 92, delta: 7, periodo: "esta semana" },
    conflictos_abiertos: { total: 12, delta: -3, periodo: "desde el lunes" },
    asistencia_promedio: { valor: 93, delta: 0, periodo: "sin cambio" },
    tramites_pendientes: { total: 7 },
    nuevos_hoy: { usuarios: 3, tramites: 2 }
  }

GET    /api/v1/stats/usuarios           [JWT + admin]
  query: ?periodo=30d|7d|1y
  returns: { por_rol, por_estado, nuevos_por_dia: [...] }

GET    /api/v1/stats/salones            [JWT + admin|coordinador]
  returns: { total, por_tipo, ocupacion_promedio, mas_usados: [...] }

GET    /api/v1/stats/carreras           [JWT + admin|director]
  returns: { carreras: [{ nombre, estudiantes, horarios_pub, asistencia_prom }] }

GET    /api/v1/stats/asistencia         [JWT + coordinador|admin]
  query: ?carrera_id=&materia_id=&periodo_id=
  returns: { promedio, distribucion, peor_asistencia: [...materias] }

GET    /api/v1/stats/calificaciones     [JWT + coordinador|admin]
  returns: { distribucion_notas, aprobacion_pct, reprobacion_pct }
```

### 3.14 MAPA — `/api/v1/mapa`

```
GET    /api/v1/mapa                     [público]
  query: ?plantel_id=
  returns: {
    svg_base: "...",   # SVG del campus completo
    edificios: [{ id, clave, nombre, coordenadas_x, coordenadas_y, ancho, alto, color }],
    puntos_interes: [PuntoInteresDTO]
  }

GET    /api/v1/mapa/ruta                [público]
  query: ?origen=edificio_id&destino=salon_id
  returns: { pasos: ["Sal del edificio A", "Gira a la derecha", ...], tiempo_estimado_min: 3 }

GET    /api/v1/mapa/buscar              [JWT]
  query: ?q=C-310|"Laboratorio de Redes"|"Cálculo I"
  returns: { salones: [...], edificios: [...], materias: [...] }
```

### 3.15 BÚSQUEDA GLOBAL — `/api/v1/buscar`

```
GET    /api/v1/buscar                   [JWT]
  query: ?q=texto&tipos=usuarios,materias,salones,tramites
  returns: {
    usuarios: [...],
    materias: [...],
    salones: [...],
    tramites: [...],
    total: N
  }
```

### 3.16 AUDIT LOG — `/api/v1/audit`

```
GET    /api/v1/audit                    [JWT + rector|admin]
  query: ?user_id=&accion=&entidad=&desde=&hasta=&page=
  returns: { data: [AuditLogDTO], total, ... }
```

---

## 4. PÁGINAS WEB — DISEÑO Y COMPORTAMIENTO

### 4.1 Públicas (sin autenticación)

#### `/` — Landing Page
- Navbar público: wordmark "Matute Guide" (Lexend 700) + "Iniciar sesión" (outline) + "Registrarse" (primary)
- Hero: D/48 "Guía tu camino en el campus" + D/20 subtítulo + botón Primary L "Explorar oferta académica" + link soft "Ver el mapa del campus"
- 3 Feature cards con icono 32px + título + descripción: Horarios inteligentes / Mapa del campus / Trámites en línea
- Sección Estadísticas: 14,218 estudiantes · 92 horarios · 44 salones — datos REALES de `/api/v1/stats/dashboard`
- Oferta académica preview: 3 carreras en ContentCards
- Footer: links institucionales + "Matute Guide · MIT License · 2026"

#### `/auth/login` — Login
- Layout split 50/50 desktop, stack mobile
- Izquierda: surface navy-950, quote en Lexend italic D/24, atribución DM Sans B/14
- Derecha: formulario con título D/24 "Inicia sesión"
- Campos: Correo institucional + Contraseña (toggle show/hide con icono)
- Link "Olvidé mi contraseña" → `/auth/password-reset`
- Primary L full-width "Iniciar sesión"
- Divider "o"
- Secondary L "Registrarse"
- Outline L "Ingresar como aspirante"
- Alert danger inline si credenciales inválidas (API error)
- Alert warning si cuenta suspendida con link "Contactar soporte"
- On success: redirect según rol:
  - estudiante → `/dashboard`
  - admin|director|coordinador → `/admin`
  - profesor → `/profesor`
  - invitado → `/oferta`

#### `/auth/register` — Registro (3 pasos)
- Progress indicator con 3 pasos numerados en la parte superior
- **Paso 1 — Datos personales:** nombre, apellido_p, apellido_m, email (@alumnos.udg.mx), contraseña (con strength indicator), confirmar contraseña
- **Paso 2 — Perfil académico:** rol (radio group visual: Estudiante/Aspirante/Profesor), plantel (select), carrera (select dinámico si rol=estudiante)
- **Paso 3 — Confirmación:** resumen de datos + checkbox "Acepto el aviso de privacidad" + link a política
- Botones: "Anterior" (outline) + "Siguiente"/"Crear cuenta" (primary)
- Validación inline en cada campo al blur

#### `/oferta` — Oferta Académica
- Datos desde `/api/v1/carreras`
- Grid 3 col desktop / 1 col mobile de ContentCards
- Cada card: nombre, descripción, duración, campos, botón "Ver plan de estudios"
- Página de detalle `/oferta/:slug`: plan de estudios completo por semestre con materias color-coded por tipo
- Empty state si no hay carreras activas

#### `/salones` — Directorio Público de Salones
- Datos desde `/api/v1/salones` + `/api/v1/edificios`
- Search input + toggle tabs por edificio (Todos · Edif. A · Edif. B · ...)
- Filter dropdown: Tipo + Capacidad mínima + Solo disponibles ahora (switch)
- Grid de SalonCards (código, tipo badge, capacidad, dot disponibilidad)
- Toggle vista tabla
- Actualización de disponibilidad_ahora cada 60s via polling

#### `/salones/:codigo` — Detalle de Salón
- Datos desde `/api/v1/salones/:id`
- Breadcrumb: Inicio / Salones / Edificio A / A-203
- Header: código D/32 + badge tipo + chip capacidad + indicador disponibilidad actual
- **Grilla de disponibilidad semanal:** 5 días × horas 07:00–20:00
  - Bloques ocupados con materia + grupo
  - Huecos libres con color surface-150
  - Leyenda: Ocupado / Libre
- Equipamiento: iconos + labels (proyector, AC, etc.)
- Botón "Ver en mapa" → `/mapa?highlight=salon_id`

#### `/mapa` — Mapa del Campus
- Datos desde `/api/v1/mapa`
- SVG interactivo del campus (edificios como polígonos)
- Sidebar izquierda: search "Buscar salón o edificio…" + filtros por tipo
- Click en edificio → expandir overlay con lista de salones
- Click en salón → panel lateral con info + disponibilidad rápida
- Filtros: todos / aulas / laboratorios / servicios / puntos de interés
- Botón "¿Cómo llegar?" entre dos puntos → ruta textual

---

### 4.2 Portal Estudiante (JWT: estudiante)

#### `/dashboard` — Dashboard Principal
- Navbar autenticado (wordmark + Salones / Horario / Mapa + avatar chip)
- Tabs underline: **Resumen · Horario {N} · Calificaciones · Asistencia {pct}% · Trámites {N}**

**Tab Resumen (datos de `/api/v1/auth/me` + horario + tramites):**
- Row de stat chips: Materias / Horas semanales / Porcentaje asistencia / Créditos
- Alert info si hay conflictos en horario
- Alert warning si hay trámites pendientes de acción
- Sección "Hoy": bloques del día con hora + materia + salon (from `/api/v1/horarios`)
- Empty state si no hay horario publicado: "Tu horario aún está vacío" + CTA "Crear mi horario"
- Sección "Próximos eventos del calendario académico": 3 eventos más cercanos
- Anuncios fijados de `/api/v1/anuncios`

**Tab Horario:**
- ScheduleGrid semana completa
- Selector periodo si hay más de uno
- Botones: "Publicar" (si borrador) / "Guardar borrador" / "Exportar PDF"
- Panel lateral toggle: "Agregar materia"
  - Select carrera → Select semestre → Select materia → Select día → Select hora → Select salon (muestra disponibilidad) → Botón "Agregar"
  - Validación de conflicto en tiempo real antes de agregar

**Tab Calificaciones:**
- Tabla: Materia / Parcial 1 / Parcial 2 / Parcial 3 / Ordinario / Final
- Badges: publicada (visible) / no publicada (gris "—")
- Promedio general al pie
- Filtro por periodo

**Tab Asistencia:**
- Por materia: barra de progreso + porcentaje + presente/ausente/justificado
- Aviso warning si < 80% en alguna materia
- Tabla de fechas con estado por bloque (al click en materia)

**Tab Trámites:**
- Lista de trámites propios con folio + tipo + estado badge + fecha
- Botón Primary "+ Nuevo trámite"
- Click en trámite → panel lateral / página de detalle con seguimiento timeline

#### `/horario` — Constructor de Horario (standalone)
- Header: periodo activo + estado del horario (badge) + botones acción
- Segmented tabs: **Semana · Día · Lista**
- ScheduleGrid interactivo:
  - Click en celda vacía → quick-add panel
  - Click en bloque → popover: detalle + botón "Eliminar bloque"
  - Drag opcional (si implementado)
- Panel lateral: "Agregar materia" con búsqueda y select de salon + disponibilidad en tiempo real
- Toast al agregar (success) o detectar conflicto (warning con detalle)
- Conflicto: bloque warning con "CONFLICTO · N clases" + CTA "REVISAR AGENDA"
- Botón "Aplicar plantilla" → modal con plantillas disponibles para su carrera/semestre

#### `/tramites` — Gestión de Trámites
- Lista de trámites del estudiante (datos reales de API)
- Botón "+ Nuevo trámite" → modal multi-step:
  - Paso 1: selección de tipo (cards con nombre + descripción + costo + tiempo)
  - Paso 2: formulario específico del trámite
  - Paso 3: subida de documentos requeridos
  - Paso 4: confirmación con folio generado
- Página de detalle `/tramites/:id`: timeline de seguimiento con timestamps

#### `/perfil` — Perfil del Estudiante
- Avatar xl con color personalizable + iniciales + upload de foto
- Datos personales con botón "Editar" inline
- Sección "Seguridad": cambio de contraseña
- Sección "Preferencias": switches de notificaciones (usar `/api/v1/notificaciones/config` si existe)

---

### 4.3 Portal Profesor (JWT: profesor)

#### `/profesor` — Dashboard Profesor
- Mis clases del día (desde bloques donde es profesor_id)
- Lista de grupos activos con conteo de estudiantes
- Acceso rápido: "Capturar calificaciones" / "Pasar lista" / "Ver horario"

#### `/profesor/horario` — Horario del Profesor
- ScheduleGrid con todas las clases donde es asignado
- Solo lectura (el profesor no construye su propio horario)

#### `/profesor/grupos/:inscripcion_id` — Lista del Grupo
- Tabla de estudiantes de ese grupo con: avatar + nombre + expediente + estado inscripción
- Sección "Calificaciones": captura de parciales, publicar calificaciones (botón separado)
- Sección "Asistencia": grid fecha × estudiante con click para marcar estado
- Botón "Pasar lista de hoy" → modal simplificado con lista vertical de estudiantes

---

### 4.4 Panel Administrativo (JWT: admin|director|coordinador)

**Layout:** Sidebar 240px (navy-800) + content area. Sidebar siempre visible en desktop.

**Sidebar secciones y navegación:**
```
Matute Guide                (wordmark)

PANEL
  🏠 Inicio
  🔔 Notificaciones  {N}

ACADÉMICO
  📅 Horarios
  📚 Materias
  🎓 Carreras
  📆 Periodos

CAMPUS
  🏢 Salones
  🗺️ Mapa
  🏛️ Edificios

COMUNIDAD
  👥 Usuarios
  👨‍🏫 Profesores
  🎒 Estudiantes
  📋 Trámites  {N pendientes}
  📢 Anuncios

SISTEMA
  📊 Reportes
  📋 Audit Log
  ⚙️ Configuración
```

#### `/admin` — Dashboard Admin
- Stat cards KPI (4 × 2 grid en mobile):
  - ESTUDIANTES ACTIVOS: valor real + trend + "vs sem. anterior"
  - HORARIOS PUBLICADOS: X/meta + trend + "esta semana"
  - CONFLICTOS ABIERTOS: N + trend + "desde el lunes"
  - ASISTENCIA PROMEDIO: % + trend + "sin cambio"
  - TRÁMITES PENDIENTES: N
  - NUEVOS HOY: usuarios + trámites
- Gráfica simple de nuevos usuarios por semana (canvas o SVG, NO librería externa)
- Últimas 10 acciones del audit log
- Trámites pendientes de atención (lista rápida)
- Anuncios activos

#### `/admin/usuarios` — Gestión de Usuarios
- Toolbar: search + filter Todos/Activos/Suspendidos + dropdown Rol + botón "+ Nuevo"
- Data table:
  - ☐ / Avatar+Nombre+email / Expediente / Carrera / Rol (RoleTag) / Estado (StatusBadge) / Acciones(⋮)
  - Row hover: surface-100 / Selected: 3px border navy
  - Acciones dropdown: Editar · Ver horario · Ver trámites · Exportar · — · Suspender · Eliminar
- Bulk actions bar (aparece al seleccionar ≥1): "X seleccionados · Suspender todos · Eliminar todos · Cancelar"
- Pagination real: Mostrando X–Y de Z · per_page selector
- **Modal Nuevo/Editar Usuario:** 440px dialog con todos los campos
- **Dialog Eliminar:** ZONA PELIGROSA + confirm input "eliminar"
- **Dialog Restablecer:** confirmar → llama a `/api/v1/users/:id/restablecer`

#### `/admin/estudiantes` — Vista específica estudiantes
- Misma estructura pero pre-filtrado rol=estudiante
- Columnas extra: Semestre / Asistencia prom
- Acceso rápido: "Ver horario" abre panel lateral con ScheduleGrid del estudiante

#### `/admin/profesores` — Vista específica profesores
- Pre-filtrado rol=profesor
- Columna extra: "Materias asignadas" (count)
- Acceso: "Ver carga académica" → panel con bloques donde es profesor

#### `/admin/horarios` — Gestión de Horarios
- Segmented tabs: **Por carrera · Por edificio · Por profesor**

**Tab Por carrera:**
- Select carrera + Select semestre + Select periodo
- ScheduleGrid consolidado con TODOS los bloques de esa carrera/semestre
- Cada bloque muestra: materia (coloreada por tipo) + salon + profesor
- Conflictos globales resaltados (warning)
- Counter "Publicados X/Y · Borradores Z · Conflictos N"
- Botón "Exportar vista PDF" + Botón danger "Cerrar periodo de inscripción" (con dialog)

**Tab Por edificio:**
- Select edificio + Select salon + Select periodo
- ScheduleGrid de disponibilidad del salon
- Color: ocupado (navy tint) / libre (surface-150)

**Tab Por profesor:**
- Autocomplete nombre del profesor
- ScheduleGrid de todos los bloques donde aparece como profesor

#### `/admin/salones` — Gestión de Salones
- Toolbar: search + tabs por edificio + filter tipo + botón "+ Nuevo salón"
- **Vista cards (default):** agrupadas por edificio
  ```
  EDIFICIO A  (15 salones)
  [card A-101] [card A-102] ... (grid 4 col)

  EDIFICIO C  (8 salones)
  [card C-310] ...
  ```
  Cada card: código D/24 + badge tipo + capacidad + dot activo + menú ⋮ (Editar / Ver horarios / Desactivar)
- **Toggle vista tabla:** CÓDIGO / EDIFICIO / TIPO / CAPACIDAD / PISO / ESTADO / ACCIONES
- **Modal Nuevo/Editar Salón:** código + edificio (select) + tipo + capacidad + piso + equipamiento (multi-select chips) + descripción
- **Modal "Ver horarios del salón":** ScheduleGrid de ese salón para el periodo activo
- **Dialog Desactivar:** confirmación simple (no destructivo)

#### `/admin/carreras` — Gestión de Carreras
- Lista de carreras como ContentCards editables
- Click → página de detalle con plan de estudios editable por semestre
- Drag-and-drop de materias entre semestres (o botones "mover")
- Dialog crear/editar carrera

#### `/admin/materias` — Gestión de Materias
- Filtrado por carrera + semestre + tipo
- Data table con: Clave / Nombre / Carrera / Semestre / Tipo / Créditos / Activa
- CRUD via modals

#### `/admin/periodos` — Gestión de Periodos Académicos
- Lista de periodos con: clave + nombre + fechas + estado (activo badge)
- Solo 1 periodo activo a la vez (toggle con dialog confirmación)
- Fechas de apertura/cierre de inscripciones editables
- Sección "Calendario académico": tabla de eventos del periodo + botón añadir evento

#### `/admin/tramites` — Gestión de Trámites
- Tabs: Pendientes · En proceso · Listos · Todos
- Data table con: Folio / Solicitante / Tipo / Estado / Fecha / Acciones
- Panel lateral al click: detalle + timeline seguimiento + botón cambiar estado
- Botón "Marcar como listo" / "Rechazar" con campo comentario
- Stats: pendientes hoy / tiempo promedio resolución

#### `/admin/anuncios` — Gestión de Anuncios
- Lista de anuncios con estado (publicado/borrador/expirado)
- Editor de anuncio: título + cuerpo (textarea) + audiencia + carrera (opcional) + fecha expiración + switch "Fijar"
- Preview antes de publicar

#### `/admin/reportes` — Reportes y Analíticas
- Tabs: Estudiantes · Asistencia · Calificaciones · Salones · Exportar
- Cada tab muestra gráficas SVG simples + tabla de datos
- Botones "Exportar CSV" + "Exportar PDF" (llamadas a API)

#### `/admin/audit` — Log de Auditoría
- Data table solo lectura: Fecha / Usuario / Acción / Entidad / IP
- Filtros: usuario + acción + fecha desde/hasta
- Click en fila → modal con payload_antes y payload_despues (JSON diff)

#### `/admin/configuracion` — Ajustes del Sistema
- Información del plantel: nombre, clave, ciudad
- Periodo activo actual
- Parámetros: máx. materias por horario, porcentaje mínimo asistencia
- Tipos de trámites CRUD

---

### 4.5 Componentes Transversales

#### Navbar (autenticado)
- Height 72px / surface navy-800
- Left: Wordmark "Matute Guide" (Lexend 700 white)
- Center links (estudiante): Salones / Horario / Mapa
- Center links (admin): — (usa sidebar)
- Right: [🔔 badge] [Avatar chip con nombre + dropdown: Mi perfil / Mi horario / Preferencias / Cerrar sesión]
- Notificaciones: bell con badge numérico, click → panel lateral con lista de notificaciones

#### Sistema de Notificaciones (real-time)
- SSE stream en `/api/v1/notificaciones/stream`
- Panel lateral (slide-in desde la derecha): lista de notificaciones con tipo + título + tiempo relativo + leída/no leída
- Al llegar notificación nueva: toast en esquina superior derecha + badge bell actualiza
- Tipos visuales:
  - 📅 horario: navy-500
  - 📊 calificacion: info
  - 📋 tramite: warning
  - 📢 anuncio: navy-800
  - ⚠️ conflicto: danger
  - ⚙️ sistema: ink-700

---

## 5. SCHEDULE GRID — ESPECIFICACIÓN COMPLETA

```css
/* Dimensiones */
.schedule-grid { display: grid; }
.time-col      { width: 56px; }
.day-col       { min-width: 84px; flex: 1; }
.hour-row      { height: 90px; }

/* Header */
.grid-header { background: var(--navy-800); color: white;
               font: 700 11px/1 var(--font-mono); letter-spacing: 0.06em; }

/* Bloques por tipo */
.bloque { border-radius: var(--r-4); padding: 4px 6px;
          width: 100%; height: 100%; overflow: hidden; cursor: pointer; }
.bloque-tronco-comun     { background: var(--navy-800); color: white; }
.bloque-area-profesional { background: var(--navy-500); color: white; }
.bloque-laboratorio      { background: var(--success);  color: white; }
.bloque-idiomas          { background: var(--navy-400); color: var(--ink-900); }
.bloque-conflicto        { background: var(--warning);  color: var(--ink-900); }

/* Contenido del bloque */
.bloque-titulo   { font: 700 12px/1.3 var(--font-body); }
.bloque-sub      { font: 400 10px/1.3 var(--font-mono); opacity: .85; margin-top: 2px; }
.bloque-conflicto-label { font: 700 9px var(--font-mono); letter-spacing: .1em;
                          text-transform: uppercase; }
```

**Interacciones JS (vanilla):**
```javascript
// Click en bloque → popover con detalle
bloque.addEventListener('click', (e) => {
  showPopover(e, {
    materia: bloque.dataset.materia,
    salon: bloque.dataset.salon,
    profesor: bloque.dataset.profesor,
    hora: `${bloque.dataset.inicio} – ${bloque.dataset.fin}`,
    actions: isOwner ? [{ label: 'Eliminar bloque', danger: true, onClick: deleteBloque }] : []
  });
});

// Click en celda vacía (si es editable) → quick-add
cell.addEventListener('click', () => openQuickAdd({ dia, hora }));
```

**Leyenda (siempre visible bajo el grid):**
```
■ Tronco común  ■ Área profesional  ■ Laboratorio  ■ Idiomas  ■ Conflicto
```

---

## 6. SISTEMA DE NOTIFICACIONES — IMPLEMENTACIÓN

### Backend (Flask-SocketIO o SSE)

```python
# Preferir SSE (Server-Sent Events) — sin dependencias extra
@app.route('/api/v1/notificaciones/stream')
@jwt_required()
def notification_stream():
    user_id = get_jwt_identity()
    def generate():
        # Polling ligero cada 10s para nuevas notificaciones
        last_check = datetime.utcnow()
        while True:
            nuevas = Notificacion.query.filter(
                Notificacion.destinatario_id == user_id,
                Notificacion.leida == False,
                Notificacion.created_at > last_check
            ).all()
            for n in nuevas:
                yield f"data: {json.dumps(n.to_dict())}\n\n"
            last_check = datetime.utcnow()
            time.sleep(10)
    return Response(generate(), mimetype='text/event-stream')

# Helper para crear notificaciones desde cualquier parte del backend
def notify(user_id, tipo, titulo, cuerpo, accion_url=None, metadata=None):
    n = Notificacion(
        destinatario_id=user_id, tipo=tipo, titulo=titulo,
        cuerpo=cuerpo, accion_url=accion_url, metadata=metadata
    )
    db.session.add(n)
    db.session.commit()
    return n
```

### Frontend (EventSource)
```javascript
const evtSource = new EventSource('/api/v1/notificaciones/stream', {
  headers: { Authorization: `Bearer ${token}` }
});
evtSource.onmessage = (e) => {
  const notif = JSON.parse(e.data);
  showToast(notif.titulo, notif.tipo);
  updateBellBadge();
  appendToNotifPanel(notif);
};
```

---

## 7. MAPA DEL CAMPUS — SVG INTERACTIVO

El mapa se sirve desde `/api/v1/mapa` y es un SVG embebido en la página.

**Estructura SVG:**
```xml
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg">
  <!-- Fondo campus -->
  <rect width="1200" height="800" fill="#F8F9FA"/>

  <!-- Edificios como grupos interactivos -->
  <g class="edificio" data-id="1" data-clave="A">
    <rect x="100" y="200" width="200" height="150"
          fill="#172846" rx="4" class="edificio-shape"/>
    <text x="200" y="280" text-anchor="middle"
          fill="white" font-family="Lexend" font-size="14">A</text>
  </g>

  <!-- Puntos de interés -->
  <g class="poi" data-tipo="cafeteria" data-id="5">
    <circle cx="400" cy="400" r="12" fill="#28A745"/>
    <!-- icono SVG inline -->
  </g>
</svg>
```

**JS interactivo:**
```javascript
document.querySelectorAll('.edificio').forEach(el => {
  el.addEventListener('click', async () => {
    const id = el.dataset.id;
    const data = await api.get(`/edificios/${id}`);
    showEdificioPanel(data); // panel lateral con salones
  });
  el.addEventListener('mouseenter', () => highlightEdificio(el));
});
```

---

## 8. FLUTTER APK — ESPECIFICACIÓN COMPLETA

### 8.1 Estructura del proyecto

```
flutter_app/
├── lib/
│   ├── main.dart
│   ├── app.dart                  ← MaterialApp, rutas, tema
│   ├── config/
│   │   └── api_config.dart       ← baseUrl, timeouts
│   ├── theme/
│   │   ├── colors.dart           ← MapColors
│   │   ├── text_styles.dart      ← MapText
│   │   └── theme.dart            ← ThemeData completo
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   ├── notification_service.dart
│   │   └── storage_service.dart  ← SharedPreferences wrapper
│   ├── models/
│   │   ├── user.dart
│   │   ├── horario.dart
│   │   ├── bloque.dart
│   │   ├── salon.dart
│   │   ├── notificacion.dart
│   │   └── tramite.dart
│   ├── providers/
│   │   ├── auth_provider.dart
│   │   ├── horario_provider.dart
│   │   └── notif_provider.dart
│   ├── widgets/
│   │   ├── schedule_grid.dart    ← Widget reutilizable
│   │   ├── status_badge.dart
│   │   ├── stat_card.dart
│   │   ├── salon_card.dart
│   │   └── notification_bell.dart
│   └── screens/
│       ├── auth/
│       │   ├── login_screen.dart
│       │   └── register_screen.dart
│       ├── student/
│       │   ├── dashboard_screen.dart
│       │   ├── horario_screen.dart
│       │   ├── calificaciones_screen.dart
│       │   ├── asistencia_screen.dart
│       │   └── tramites_screen.dart
│       ├── salones/
│       │   ├── salones_screen.dart
│       │   └── salon_detail_screen.dart
│       ├── mapa/
│       │   └── mapa_screen.dart
│       ├── admin/
│       │   ├── admin_dashboard_screen.dart
│       │   ├── admin_usuarios_screen.dart
│       │   ├── admin_horarios_screen.dart
│       │   └── admin_salones_screen.dart
│       └── shared/
│           ├── perfil_screen.dart
│           └── notificaciones_screen.dart
├── pubspec.yaml
└── android/
    └── app/
        └── build.gradle
```

### 8.2 pubspec.yaml

```yaml
name: matute_guide
description: Plataforma escolar UDG

environment:
  sdk: ">=3.0.0 <4.0.0"
  flutter: ">=3.10.0"

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  provider: ^6.1.2
  shared_preferences: ^2.2.3
  google_fonts: ^6.2.1
  intl: ^0.19.0
  fl_chart: ^0.68.0
  flutter_svg: ^2.0.10+1
  cached_network_image: ^3.3.1
  go_router: ^13.2.0
  flutter_local_notifications: ^17.2.1+2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

### 8.3 Tema Flutter (MapColors + MapText)

```dart
// theme/colors.dart
class MapColors {
  static const navy950  = Color(0xFF0B1423);
  static const navy900  = Color(0xFF031633);
  static const navy800  = Color(0xFF172846);   // primary
  static const navy700  = Color(0xFF233C5B);
  static const navy600  = Color(0xFF304B7A);
  static const navy500  = Color(0xFF3C61A5);
  static const navy400  = Color(0xFF6DB4D2);
  static const navy200  = Color(0xFFCFE2FF);
  static const surface100 = Color(0xFFF8F9FA);
  static const surface0   = Color(0xFFFFFFFF);
  static const ink900   = Color(0xFF212529);
  static const ink700   = Color(0xFF495057);
  static const ink500   = Color(0xFF9899A8);
  static const ink400   = Color(0xFFADB5BD);
  static const line300  = Color(0xFFDEE2E6);
  static const success  = Color(0xFF28A745);
  static const danger   = Color(0xFFDC3545);
  static const warning  = Color(0xFFF2B705);
  static const info     = Color(0xFF0D6EFD);

  // Schedule block colors
  static const bloqueTroncoComun     = navy800;
  static const bloqueAreaProfesional = navy500;
  static const bloqueLaboratorio     = success;
  static const bloqueIdiomas         = navy400;
  static const bloqueConflicto       = warning;

  static Color statusColor(String estado) => switch (estado) {
    'activo'      => success,
    'suspendido'  => warning,
    'inactivo'    => ink400,
    'eliminado'   => ink700,
    _             => ink400,
  };
}

// theme/text_styles.dart
class MapText {
  static TextStyle display(double size, {FontWeight w = FontWeight.w700, Color? color}) =>
      GoogleFonts.lexend(fontSize: size, fontWeight: w, color: color ?? MapColors.ink900);

  static TextStyle body(double size, {FontWeight w = FontWeight.w400, Color? color}) =>
      GoogleFonts.dmSans(fontSize: size, fontWeight: w, color: color ?? MapColors.ink900);

  static TextStyle mono(double size, {FontWeight w = FontWeight.w400, Color? color}) =>
      GoogleFonts.dmMono(fontSize: size, fontWeight: w, color: color ?? MapColors.ink700);

  // Escalas predefinidas
  static final d32 = display(32);
  static final d24 = display(24);
  static final d20 = display(20, w: FontWeight.w600);
  static final b16 = body(16);
  static final b14 = body(14);
  static final b12 = body(12);
  static final b10 = mono(10, w: FontWeight.w700);  // badges
}
```

### 8.4 Pantallas Flutter

**LoginScreen:** TextField email + TextField password (obscure toggle) + ElevatedButton navy-800 + SnackBar en error + Navigator.pushReplacement al dashboard según rol.

**DashboardScreen (estudiante):** AppBar navy-800 + BottomNavigationBar (Inicio/Horario/Salones/Perfil) + TabBarView (Resumen/Calificaciones/Asistencia/Trámites).

**HorarioScreen:** CustomScrollView con SliverToBoxAdapter. Widget ScheduleGrid en Flutter:
- Tabla scrollable horizontal + vertical
- Container con color según tipo de bloque
- GestureDetector → showModalBottomSheet con detalle
- Bloque conflicto: borde warning + texto "CONFLICTO"

**SalonesScreen:** SearchBar + ListView agrupada por edificio (ExpansionTile) + SalonCard widget.

**SalonDetailScreen:** Scaffold con CustomScrollView + SliverAppBar (código grande) + grilla disponibilidad.

**AdminDashboardScreen:** Drawer (sidebar) + GridView 2×3 de StatCards.

**AdminUsuariosScreen:** SearchBar + ListView de usuarios con ListTile + StatusBadge widget + PopupMenuButton.

**NotificacionesScreen:** ListView de notificaciones con tile: icono tipo + título + tiempo relativo + leída/no leída.

### 8.5 Gestión de Auth en Flutter

```dart
class AuthService {
  static const _tokenKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _userKey = 'user_data';

  static Future<void> saveTokens(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, access);
    await prefs.setString(_refreshKey, refresh);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<bool> refreshToken() async {
    final refresh = await getRefreshToken();
    if (refresh == null) return false;
    try {
      final response = await ApiService.post('/auth/refresh', { 'refresh_token': refresh });
      await saveTokens(response['access_token'], refresh);
      return true;
    } catch (_) {
      await logout();
      return false;
    }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_refreshKey);
    await prefs.remove(_userKey);
  }
}

// ApiService: interceptor para 401 → refresh → retry → logout si falla
```

---

## 9. SEED DATA — DATOS REALISTAS

```python
# seed.py — genera datos que parecen reales

PLANTELES = [
  { "nombre": "CUValles", "clave": "CUV", "ciudad": "Ameca" }
]

USUARIOS = [
  { "nombre": "Diego", "apellido_p": "Hernández", "email": "admin@udg.mx",
    "rol": "admin", "password": "Admin1234!" },
  { "nombre": "Álvaro", "apellido_p": "Díaz", "apellido_m": "Ramírez",
    "email": "alvaro.diaz@alumnos.udg.mx", "rol": "estudiante",
    "expediente": "218 492", "semestre_actual": 4, "carrera": "tec-informatica" },
  { "nombre": "Yael Omar", "apellido_p": "Vega",
    "email": "yael.omar@alumnos.udg.mx", "rol": "estudiante",
    "expediente": "218 731", "semestre_actual": 2, "carrera": "tec-biotecnologia" },
  { "nombre": "Jorge", "apellido_p": "Méndez",
    "email": "jorge.mendez@udg.mx", "rol": "profesor", "expediente": "P-218" },
  { "nombre": "Rocío", "apellido_p": "Castellanos",
    "email": "rocio.castellanos@alumnos.udg.mx", "rol": "estudiante",
    "expediente": "218 902", "semestre_actual": 6, "carrera": "tec-energias" },
]

CARRERAS = [
  { "nombre": "Tecnólogo Profesional en Informática",
    "slug": "tec-informatica", "campos": "desarrollo, soporte, redes y datos",
    "duracion_semestres": 8 },
  { "nombre": "Tecnólogo Profesional en Biotecnología",
    "slug": "tec-biotecnologia", "campos": "laboratorio, agroindustria, salud",
    "duracion_semestres": 8 },
  { "nombre": "Tecnólogo Profesional en Energías Alternas",
    "slug": "tec-energias", "campos": "solar, eólica, eficiencia energética",
    "duracion_semestres": 8 },
]

# Edificios: A (15), B (10), C (8), CELE (6), LAB (5) = 44 salones totales
EDIFICIOS = [
  { "clave": "A", "nombre": "Edificio A", "coord_x": 100, "coord_y": 200 },
  { "clave": "B", "nombre": "Edificio B", "coord_x": 350, "coord_y": 200 },
  { "clave": "C", "nombre": "Edificio C", "coord_x": 600, "coord_y": 200 },
  { "clave": "CELE", "nombre": "CELE", "coord_x": 100, "coord_y": 500 },
  { "clave": "LAB", "nombre": "Laboratorios", "coord_x": 350, "coord_y": 500 },
]

# Materias: 4 semestres × ~6 materias × 3 carreras = 72 materias
# Tipos distribuidos: tronco_comun / area_profesional / laboratorio / idiomas

# Horario de Álvaro (4to semestre Informática):
# Lun 07:00-09:00: Cálculo I (A-203, Méndez)        — tronco_comun
# Lun 09:00-11:00: Tecnología en la Contabilidad (B-110, López) — area_profesional
# Mar 09:00-11:00: Tecnología en la Contabilidad (B-110, López)
# Mar 11:00-13:00: Programación Web (LAB-4, Reyes)  — laboratorio
# Mié 07:00-09:00: Cálculo I (A-203, Méndez)
# Mié 11:00-13:00: Programación Web (LAB-4, Reyes)
# Mié 11:00-13:00: Bases de Datos (LAB-2, Torres)   ← CONFLICTO REAL
# Jue 09:00-11:00: Tecnología en la Contabilidad (B-110, López)
# Jue 13:00-15:00: Inglés VII (CELE-2, Brown)       — idiomas
# Vie 07:00-09:00: Cálculo I (A-203, Méndez)
# Vie 13:00-15:00: Inglés VII (CELE-2, Brown)
# Mar 15:00-17:00: Estadística (A-110, Vargas)
# Jue 15:00-17:00: Estadística (A-110, Vargas)
```

---

## 10. PÁGINA DE COMPONENTES `/components`

Solo en `DEBUG=True`. Una sola página larga que exhibe todos los componentes con datos reales (no mock inline). Secciones con anchor links:

```
01 Colores — swatches de todos los tokens con hex y nombre
02 Tipografía — escala display (D/96 → D/20) y body (B/20 → B/10)
03 Botones — grid 6 variantes × 3 tamaños + disabled
04 Inputs — todos los estados (default/focus/error/success/disabled)
05 Form controls — checkbox, radio, switch, slider
06 Badges y tags — StatusBadge × 6 estados + RoleTag × 5 roles
07 Avatars — 5 tamaños + status dots + stack
08 Tabs — underline + segmented
09 Alerts — 4 semánticos (con dismiss)
10 Toasts — botones para disparar cada tipo
11 Dialogs — botones para abrir: confirmation + destructive
12 Dropdown menu — con keyboard shortcuts
13 Tooltip + Breadcrumbs
14 Paginación — 3 variantes (<5, 5-8, >8 con elipsis)
15 Cards — InfoCard × 3 estados + ContentCard + SalonCard
16 Stat cards — KPI con trend y sparkline
17 Data table — con datos del seed, paginada, con acciones
18 Empty states — vacío + sin resultados + error
19 Schedule grid — semana completa con conflicto incluido
20 Notificaciones — panel lateral + toast demo
```

---

## 11. MEJORES PRÁCTICAS TÉCNICAS

### Flask
- Application Factory pattern (`create_app()`)
- Blueprints por dominio: `auth`, `users`, `academic`, `campus`, `schedules`, `tramites`, `notifications`, `stats`, `maps`
- `flask-migrate` para todas las migraciones — nunca `db.create_all()` en producción
- Environment variables: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `FLASK_ENV`
- Rate limiting en endpoints de auth (flask-limiter: 5 req/min en login)
- CORS configurado explícitamente (no `*` en producción)
- Logging estructurado con nivel apropiado por entorno
- Health check: `GET /health` → `{ status: "ok", db: "ok", version: "1.0.0" }`

### SQLAlchemy
- Relaciones con `lazy='select'` por defecto, `lazy='joined'` solo donde se siempre necesite
- Índices en: `user.email`, `user.estado`, `notificacion.destinatario_id`, `notificacion.leida`, `bloque.horario_id`
- Transacciones explícitas para operaciones que modifican múltiples tablas
- `db.session.rollback()` en todos los `except`

### Seguridad
- Passwords con `bcrypt` (cost factor 12)
- JWT access tokens: 1h TTL. Refresh tokens: 30d TTL con rotación.
- Blacklist de JTI revocados en tabla `refresh_token`
- Input sanitization en todos los endpoints
- No exponer stack traces en producción (handler de error genérico)
- Headers de seguridad: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`

### CSS / Frontend
- Cero valores hardcodeados — SOLO variables CSS `var(--token)`
- BEM light: `.componente__elemento--modificador`
- Mobile-first: breakpoints en 768px (tablet) y 1024px (desktop)
- Transiciones: `150ms ease` para hover, `250ms ease` para dialogs/panels
- Focus visible obligatorio en todos los interactivos (3px navy outline)
- `prefers-reduced-motion` respetado

### Flutter
- Provider para estado global (auth, notificaciones)
- GoRouter para navegación con redirección auth
- `ApiService`: método central con interceptor 401 → refresh → retry
- Todos los colores: `MapColors.*` — nunca `Color(0xFF...)` inline
- Todos los textos: `MapText.*` — nunca `TextStyle(...)` inline
- Widgets de carga: `CircularProgressIndicator` con color `MapColors.navy800`

---

## 12. DEFINITION OF DONE (DoD)

### Fase 1 — Backend ✓
- [ ] `flask run` sin errores en modo development
- [ ] `python seed.py` puebla la BD completamente (sin errores)
- [ ] `GET /health` retorna `{"status": "ok"}`
- [ ] Todos los endpoints de auth funcionan (curl-testable)
- [ ] JWT válido requerido en rutas protegidas → 401 sin token
- [ ] Rol incorrecto → 403
- [ ] Soft-delete funciona: usuario eliminado no aparece en listados normales
- [ ] Conflicto de bloque detectado → `conflicto=True` en BD + advertencia en response
- [ ] AuditLog creado para: user.delete, user.suspend, horario.publish
- [ ] Rate limiting activo en `/auth/login`
- [ ] CORS configurado
- [ ] Todos los endpoints retornan JSON válido con estructura correcta
- [ ] Endpoint de búsqueda global funciona

### Fase 2 — Web ✓
- [ ] `/components` muestra los 21 componentes completos
- [ ] CERO colores hardcodeados en HTML/CSS
- [ ] Todas las páginas públicas accesibles sin token
- [ ] Auth: login/logout/register funciona end-to-end
- [ ] JWT guardado en cookie httpOnly, enviado automáticamente
- [ ] Redirect correcto según rol después de login
- [ ] Dashboard estudiante: tabs funcionan, datos reales del seed
- [ ] ScheduleGrid muestra el horario de Álvaro con el conflicto visual en Mié 11:00
- [ ] Notificaciones SSE: al crear notificación via API → aparece en bell sin reload
- [ ] Admin usuarios: search/filter/pagination con datos reales
- [ ] Admin salones: CRUD completo funcional
- [ ] Admin horarios: 3 vistas muestran datos reales
- [ ] Mapa: SVG interactivo carga y responde a clicks
- [ ] Salones públicos: disponibilidad en tiempo real (actualiza sin recarga)
- [ ] Trámites: crear trámite → folio generado → notificación al admin
- [ ] Responsive: todas las páginas funcionales en 375px (mobile)
- [ ] WCAG AA verificado en pares texto/fondo principales
- [ ] Copy en español, sin errores ortográficos, acentos correctos

### Fase 3 — Flutter APK ✓
- [ ] `flutter build apk --release` compila sin errores ni warnings críticos
- [ ] APK instala correctamente en Android 10+
- [ ] Login funciona contra Flask local (configurable via `api_config.dart`)
- [ ] HorarioScreen muestra ScheduleGrid con colores correctos por tipo
- [ ] Bloque conflicto muestra color warning + label "CONFLICTO"
- [ ] SalonesScreen lista edificios y salones con disponibilidad
- [ ] Notificaciones: recibe y muestra nuevas notificaciones
- [ ] 401 en cualquier request → redirect a LoginScreen automático
- [ ] Refresh token funciona: acceso continuo sin re-login manual
- [ ] AdminDashboard muestra KPI stats si rol=admin
- [ ] CERO `Color(0xFF...)` hardcodeados — todo usa `MapColors.*`
- [ ] CERO `TextStyle(...)` inline — todo usa `MapText.*`

---

## 13. /goal PARA CLAUDE CODE

```
/goal Build Matute Guide — production-grade school management platform for Universidad de Guadalajara.

DESIGN SYSTEM (READ FIRST — apply to every UI element):
https://claude.ai/design/p/019e1eed-86d4-764b-8fe6-e93ca122fced?file=MapSchool+Design+System-print.html&via=share
Tokens: navy #172846 primary, Lexend display, DM Sans body, DM Mono mono, 4px grid, WCAG AA.

REPO: https://github.com/MapSchool1/web
REQUIREMENTS: MATUTE_GUIDE_PRD.md (full spec with all models, endpoints, screens, components)

ABSOLUTE RULES (never violate):
1. ZERO hardcoded data — all from DB via API
2. ZERO hardcoded colors — CSS vars on web, MapColors.* on Flutter
3. Spanish copy, second-person, accent-correct throughout
4. Every list view needs an empty state
5. Every form needs inline validation
6. Soft-delete only for users/horarios/materias — never DROP rows
7. Audit log for every privileged or destructive action
8. WCAG AA for all text/background pairs

==== PHASE 1: BACKEND FOUNDATION ====
DELIVERABLES:
  - All 12 models (Plantel, User, RefreshToken, AuditLog, Carrera, Materia, PeriodoAcademico,
    CalendarioAcademico, Edificio, Salon, Horario, Bloque, PlantillaHorario, Inscripcion,
    Calificacion, RegistroAsistencia, TipoTramite, Tramite, SeguimientoTramite,
    Notificacion, Anuncio, PuntoInteres)
  - All migrations (flask-migrate, NOT db.create_all)
  - seed.py with realistic data: 5 users, 3 carreras, 44 salones across 5 edificios,
    72 materias, 1 periodo activo, 1 full student horario WITH a real conflict (Wed 11:00)
  - All API blueprints: auth, users, academic (carreras/materias/periodos),
    campus (edificios/salones), horarios (with conflict detection), inscripciones
    (with calificaciones/asistencia), tramites, notifications (SSE), stats, mapa, search
  - JWT auth (access 1h + refresh 30d with rotation and blacklist)
  - Role-based @roles_required decorator
  - Rate limiting on /auth/login (5 req/min)
  - CORS configured
  - AuditLog written for: user.delete, user.suspend, horario.publish
  - GET /health endpoint

DONE WHEN: curl against all endpoints returns correct JSON. seed.py runs cleanly.
Paste curl output for: POST /auth/login, GET /api/v1/users, GET /api/v1/salones,
GET /api/v1/horarios/:id (Álvaro's), GET /api/v1/stats/dashboard

==== PHASE 2: WEB FRONTEND ====
DELIVERABLES:
  - app/static/css/tokens.css — ALL MapSchool CSS custom properties (exact values)
  - app/templates/base.html — Navbar (72px, navy-800, Lexend wordmark, role-aware)
  - app/templates/components/ — ALL 21 MapSchool components as Jinja2 macros + CSS:
    Button (6 variants × S/M/L), Input (all states), Checkbox, Radio, Switch, Slider,
    StatusBadge (semantic), RoleTag, Avatar (5 sizes + stack), TabsUnderline, TabsSegmented,
    Alert (4 semantic), Toast (JS auto-dismiss 6s + progress bar), Dialog (confirm + destructive),
    DropdownMenu, Tooltip (400ms delay), Breadcrumbs, Pagination, Navbar, Sidebar,
    InfoCard, ContentCard, SalonCard, StatCard (with sparkline), DataTable (sticky + hover),
    EmptyState (3 variants), ScheduleGrid (colored blocks + conflict + legend + popover)
  - GET /components — demo page showing all 21 components with REAL data from seed
  - 14 web pages wired to real API data (ZERO mock data in templates):
    / (landing with real stats), /auth/login, /auth/register (3-step),
    /dashboard (student: 5 tabs, real horario, real grades), /horario (interactive builder),
    /tramites, /perfil,
    /salones (public directory, real-time availability), /salones/:codigo (week grid),
    /oferta (real carreras), /mapa (interactive SVG from API),
    /admin (KPI from /stats), /admin/usuarios (full CRUD + bulk),
    /admin/horarios (3 views: carrera/edificio/profesor), /admin/salones (CRUD + modal),
    /admin/carreras, /admin/materias, /admin/periodos, /admin/tramites,
    /admin/anuncios, /admin/reportes, /admin/audit, /admin/configuracion,
    /profesor, /profesor/horario, /profesor/grupos/:id
  - SSE notifications: EventSource on all authenticated pages, bell badge, slide panel
  - Interactive map: SVG from API, clickable buildings, panel with salones
  - JWT in httpOnly cookie, auto-sent on requests
  - Redirect by role after login
  - All pages responsive (375px mobile)
  - JS for: Toast (6s + progress), Dialog open/close, Dropdown, Tooltip, Schedule popover,
    Notification SSE, Map interactions, Calendar drag/click

DONE WHEN: All 14 pages load with real data. /components shows all 21. ScheduleGrid
shows Álvaro's horario with conflict highlighted. SSE notifications arrive without reload.
Screenshot /components and /admin and /dashboard.

==== PHASE 3: FLUTTER APK ====
DELIVERABLES:
  - Flutter project in flutter_app/ with structure from spec
  - MapColors + MapText exactly matching CSS tokens (verify hex values match)
  - GoRouter with auth guard (redirect to login if no token)
  - Provider state management for auth + notifications + horario
  - ApiService with: all endpoints from spec, JWT interceptor, 401 → refresh → retry → logout
  - 13 screens: LoginScreen, RegisterScreen, DashboardScreen (BottomNav + TabBar),
    HorarioScreen (scrollable ScheduleGrid widget with tap-for-detail),
    CalificacionesScreen, AsistenciaScreen, TramitesScreen,
    SalonesScreen (grouped by edificio), SalonDetailScreen (availability grid),
    MapaScreen (flutter_svg + tap interactions), PerfilScreen,
    AdminDashboardScreen (Drawer + StatCards), AdminUsuariosScreen,
    NotificacionesScreen
  - ScheduleGrid Flutter widget: horizontal + vertical scroll, colored blocks by tipo,
    conflict block (warning border + CONFLICTO label), tap → BottomSheet with detail
  - Local notifications via flutter_local_notifications
  - flutter build apk --release

DONE WHEN: APK installs on Android 10+. Login works against local Flask.
HorarioScreen shows Álvaro's schedule with conflict. Admin sees KPI stats.
Paste build output confirming release APK path.

==== SKILLS TO USE ====
Before coding frontend: read /mnt/skills/public/frontend-design/SKILL.md
Before creating any file: check /mnt/skills/public/ for relevant skills
If a skill is missing: search PyPI/pub.dev/npm for the best library and install it

==== HOW TO EXECUTE ====
Execute phases sequentially. Within each phase:
1. Plan the work for this phase (list files to create/modify)
2. Implement incrementally (models → migrations → seed → endpoints → tests)
3. Verify each section works before moving on
4. Report completion with evidence (curl output / screenshot path / build log)
Never jump to next phase without confirming current phase DoD.
Ask for clarification ONLY if a requirement is genuinely ambiguous — otherwise execute.
```
