from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


ESTADOS_INSCRIPCION = ('activa', 'baja', 'baja_justificada', 'aprobada', 'reprobada')
TIPOS_CALIFICACION = ('parcial_1', 'parcial_2', 'parcial_3',
                      'ordinario', 'extraordinario', 'final')
ESTADOS_ASISTENCIA = ('presente', 'ausente', 'justificado', 'retardo')


class Inscripcion(db.Model):
    __tablename__ = 'inscripcion'
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                              nullable=False, index=True)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'),
                           nullable=False, index=True)
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodo_academico.id'),
                           nullable=False, index=True)
    grupo = db.Column(db.String(10))
    profesor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    estado = db.Column(db.Enum(*ESTADOS_INSCRIPCION, name='estado_inscr_enum'),
                       default='activa', index=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    materia = db.relationship('Materia', lazy='select')
    profesor = db.relationship('User', foreign_keys=[profesor_id], lazy='select')
    calificaciones = db.relationship('Calificacion', backref='inscripcion',
                                     cascade='all, delete-orphan', lazy='select')
    asistencias = db.relationship('RegistroAsistencia', backref='inscripcion',
                                  cascade='all, delete-orphan', lazy='select')

    def to_dict(self, expand=True):
        data = {
            'id': self.id,
            'estudiante_id': self.estudiante_id,
            'materia_id': self.materia_id,
            'periodo_id': self.periodo_id,
            'grupo': self.grupo,
            'profesor_id': self.profesor_id,
            'estado': self.estado,
        }
        if expand and self.materia:
            data['materia'] = self.materia.to_dict()
        if expand and self.profesor:
            data['profesor'] = {
                'id': self.profesor.id,
                'nombre_completo': self.profesor.nombre_completo,
            }
        return data


class Calificacion(db.Model):
    __tablename__ = 'calificacion'
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripcion.id'),
                               nullable=False, index=True)
    tipo = db.Column(db.Enum(*TIPOS_CALIFICACION, name='tipo_calif_enum'),
                     nullable=False)
    valor = db.Column(db.Numeric(4, 2))
    observaciones = db.Column(db.Text)
    capturado_por = db.Column(db.Integer, db.ForeignKey('user.id'))
    capturado_at = db.Column(db.DateTime, default=utcnow)
    publicado = db.Column(db.Boolean, default=False)
    publicado_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'inscripcion_id': self.inscripcion_id,
            'tipo': self.tipo,
            'valor': float(self.valor) if self.valor is not None else None,
            'observaciones': self.observaciones,
            'publicado': self.publicado,
            'publicado_at': self.publicado_at.isoformat() + 'Z' if self.publicado_at else None,
            'capturado_at': self.capturado_at.isoformat() + 'Z' if self.capturado_at else None,
        }


class RegistroAsistencia(db.Model):
    __tablename__ = 'registro_asistencia'
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripcion.id'),
                               nullable=False, index=True)
    bloque_id = db.Column(db.Integer, db.ForeignKey('bloque.id'),
                          nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    estado = db.Column(db.Enum(*ESTADOS_ASISTENCIA, name='estado_asist_enum'))
    justificacion = db.Column(db.Text)
    registrado_por = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'inscripcion_id': self.inscripcion_id,
            'bloque_id': self.bloque_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'estado': self.estado,
            'justificacion': self.justificacion,
        }
