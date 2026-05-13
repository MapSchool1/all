from datetime import datetime
import bcrypt
from app.extensions import db


def utcnow():
    return datetime.utcnow()


ROLES = ('rector', 'director', 'coordinador', 'profesor',
         'admin', 'estudiante', 'invitado', 'aspirante')
ESTADOS_USER = ('activo', 'suspendido', 'inactivo', 'eliminado')


class Plantel(db.Model):
    __tablename__ = 'plantel'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    clave = db.Column(db.String(20), unique=True, nullable=False)
    ciudad = db.Column(db.String(100))
    direccion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    carreras = db.relationship('Carrera', backref='plantel', lazy='select')
    edificios = db.relationship('Edificio', backref='plantel', lazy='select')
    usuarios = db.relationship('User', backref='plantel', lazy='select')
    periodos = db.relationship('PeriodoAcademico', backref='plantel', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'clave': self.clave,
            'ciudad': self.ciudad,
            'direccion': self.direccion,
            'activo': self.activo,
        }


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_p = db.Column(db.String(100), nullable=False)
    apellido_m = db.Column(db.String(100))
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.Enum(*ROLES, name='roles_enum'),
                    default='estudiante', nullable=False, index=True)
    estado = db.Column(db.Enum(*ESTADOS_USER, name='estado_user_enum'),
                       default='activo', nullable=False, index=True)
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'), nullable=True)
    expediente = db.Column(db.String(30), unique=True, nullable=True)
    avatar_color = db.Column(db.String(7), default='#172846')
    telefono = db.Column(db.String(20))
    semestre_actual = db.Column(db.Integer)
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'), nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    ultimo_acceso = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    horarios = db.relationship('Horario', backref='usuario',
                               foreign_keys='Horario.user_id', lazy='select')
    inscripciones = db.relationship('Inscripcion', backref='estudiante',
                                    foreign_keys='Inscripcion.estudiante_id',
                                    lazy='select')

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt(12)
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'),
                                  self.password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False

    @property
    def nombre_completo(self):
        return ' '.join(filter(None, [self.nombre, self.apellido_p, self.apellido_m]))

    @property
    def iniciales(self):
        a = (self.nombre or '').strip()[:1].upper()
        b = (self.apellido_p or '').strip()[:1].upper()
        return f'{a}{b}' or '·'

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def to_dict(self, include_relations=True):
        data = {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido_p': self.apellido_p,
            'apellido_m': self.apellido_m,
            'nombre_completo': self.nombre_completo,
            'iniciales': self.iniciales,
            'rol': self.rol,
            'estado': self.estado,
            'expediente': self.expediente,
            'avatar_color': self.avatar_color,
            'telefono': self.telefono,
            'semestre_actual': self.semestre_actual,
            'ultimo_acceso': self.ultimo_acceso.isoformat() + 'Z' if self.ultimo_acceso else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
        if include_relations:
            data['plantel'] = self.plantel.to_dict() if self.plantel else None
            if self.carrera_id:
                from app.models.academico import Carrera
                c = Carrera.query.get(self.carrera_id)
                data['carrera'] = c.to_dict_short() if c else None
            else:
                data['carrera'] = None
        return data


class RefreshToken(db.Model):
    __tablename__ = 'refresh_token'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False, index=True)
    token_jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='refresh_tokens', lazy='select')


class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    accion = db.Column(db.String(100), nullable=False, index=True)
    entidad = db.Column(db.String(50), index=True)
    entidad_id = db.Column(db.Integer)
    payload_antes = db.Column(db.JSON)
    payload_despues = db.Column(db.JSON)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    user = db.relationship('User', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'usuario': self.user.nombre_completo if self.user else None,
            'accion': self.accion,
            'entidad': self.entidad,
            'entidad_id': self.entidad_id,
            'payload_antes': self.payload_antes,
            'payload_despues': self.payload_despues,
            'ip': self.ip,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
