from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


TIPOS_MATERIA = ('tronco_comun', 'area_profesional', 'laboratorio', 'idiomas')
TIPOS_EVENTO = ('examen', 'vacaciones', 'evento', 'feriado', 'entrega', 'otro')
AUDIENCIAS = ('todos', 'estudiantes', 'profesores', 'admin')


class Carrera(db.Model):
    __tablename__ = 'carrera'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    nombre_corto = db.Column(db.String(50))
    slug = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    duracion_semestres = db.Column(db.Integer, default=8)
    creditos_totales = db.Column(db.Integer, default=300)
    campos = db.Column(db.String(255))
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'))
    activa = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    materias = db.relationship('Materia', backref='carrera', lazy='select')

    def to_dict_short(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto,
            'slug': self.slug,
        }

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto,
            'slug': self.slug,
            'descripcion': self.descripcion,
            'duracion_semestres': self.duracion_semestres,
            'creditos_totales': self.creditos_totales,
            'campos': self.campos,
            'plantel_id': self.plantel_id,
            'activa': self.activa,
        }


class Materia(db.Model):
    __tablename__ = 'materia'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    nombre_corto = db.Column(db.String(80))
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'),
                           nullable=False, index=True)
    semestre = db.Column(db.Integer, nullable=False, index=True)
    tipo = db.Column(db.Enum(*TIPOS_MATERIA, name='tipo_materia_enum'),
                     nullable=False)
    creditos = db.Column(db.Integer, default=6)
    horas_teoria = db.Column(db.Integer, default=2)
    horas_practica = db.Column(db.Integer, default=2)
    prerequisitos = db.Column(db.JSON)
    activa = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clave': self.clave,
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto or self.nombre,
            'carrera_id': self.carrera_id,
            'carrera_nombre': self.carrera.nombre if self.carrera else None,
            'semestre': self.semestre,
            'tipo': self.tipo,
            'creditos': self.creditos,
            'horas_teoria': self.horas_teoria,
            'horas_practica': self.horas_practica,
            'prerequisitos': self.prerequisitos or [],
            'activa': self.activa,
        }


class PeriodoAcademico(db.Model):
    __tablename__ = 'periodo_academico'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    apertura_inscripciones = db.Column(db.DateTime)
    cierre_inscripciones = db.Column(db.DateTime)
    activo = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    eventos = db.relationship('CalendarioAcademico', backref='periodo', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'clave': self.clave,
            'nombre': self.nombre,
            'plantel_id': self.plantel_id,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'apertura_inscripciones': self.apertura_inscripciones.isoformat() + 'Z' if self.apertura_inscripciones else None,
            'cierre_inscripciones': self.cierre_inscripciones.isoformat() + 'Z' if self.cierre_inscripciones else None,
            'activo': self.activo,
        }


class CalendarioAcademico(db.Model):
    __tablename__ = 'calendario_academico'
    id = db.Column(db.Integer, primary_key=True)
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodo_academico.id'),
                           index=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Enum(*TIPOS_EVENTO, name='tipo_evento_enum'))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    aplica_a = db.Column(db.Enum(*AUDIENCIAS, name='audiencia_evento_enum'),
                         default='todos')
    color = db.Column(db.String(7))

    def to_dict(self):
        return {
            'id': self.id,
            'periodo_id': self.periodo_id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'aplica_a': self.aplica_a,
            'color': self.color,
        }
