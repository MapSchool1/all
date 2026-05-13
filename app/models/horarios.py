from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


DIAS = ('lun', 'mar', 'mie', 'jue', 'vie', 'sab')
DIAS_LABEL = {'lun': 'Lunes', 'mar': 'Martes', 'mie': 'Miércoles',
              'jue': 'Jueves', 'vie': 'Viernes', 'sab': 'Sábado'}
TIPOS_SESION = ('teoria', 'practica', 'laboratorio', 'examen')
ESTADOS_HORARIO = ('borrador', 'en_revision', 'publicado', 'archivado')


class Horario(db.Model):
    __tablename__ = 'horario'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False, index=True)
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodo_academico.id'),
                           nullable=False, index=True)
    nombre = db.Column(db.String(100))
    estado = db.Column(db.Enum(*ESTADOS_HORARIO, name='estado_horario_enum'),
                       default='borrador', index=True)
    total_creditos = db.Column(db.Integer, default=0)
    total_horas = db.Column(db.Integer, default=0)
    tiene_conflictos = db.Column(db.Boolean, default=False)
    publicado_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    bloques = db.relationship('Bloque', backref='horario',
                              cascade='all, delete-orphan', lazy='select')
    periodo = db.relationship('PeriodoAcademico', lazy='select')

    def to_dict(self, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'periodo_id': self.periodo_id,
            'periodo_clave': self.periodo.clave if self.periodo else None,
            'nombre': self.nombre or f'Horario {self.periodo.clave if self.periodo else ""}',
            'estado': self.estado,
            'total_creditos': self.total_creditos,
            'total_horas': self.total_horas,
            'tiene_conflictos': self.tiene_conflictos,
            'publicado_at': self.publicado_at.isoformat() + 'Z' if self.publicado_at else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'bloques_count': len(self.bloques) if self.bloques else 0,
        }
        if include_user and self.usuario:
            data['usuario'] = {
                'id': self.usuario.id,
                'nombre_completo': self.usuario.nombre_completo,
                'expediente': self.usuario.expediente,
            }
        return data


class Bloque(db.Model):
    __tablename__ = 'bloque'
    id = db.Column(db.Integer, primary_key=True)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'),
                           nullable=False, index=True)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'),
                           nullable=False)
    salon_id = db.Column(db.Integer, db.ForeignKey('salon.id'), nullable=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    dia = db.Column(db.Enum(*DIAS, name='dia_enum'), nullable=False, index=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    tipo_sesion = db.Column(db.Enum(*TIPOS_SESION, name='tipo_sesion_enum'),
                            default='teoria')
    conflicto = db.Column(db.Boolean, default=False, index=True)
    conflicto_con = db.Column(db.JSON)
    notas = db.Column(db.Text)

    materia = db.relationship('Materia', lazy='select')
    profesor = db.relationship('User', foreign_keys=[profesor_id], lazy='select')

    def to_dict(self, expand=True):
        data = {
            'id': self.id,
            'horario_id': self.horario_id,
            'materia_id': self.materia_id,
            'salon_id': self.salon_id,
            'profesor_id': self.profesor_id,
            'dia': self.dia,
            'dia_label': {'lun': 'Lun', 'mar': 'Mar', 'mie': 'Mié',
                          'jue': 'Jue', 'vie': 'Vie', 'sab': 'Sáb'}.get(self.dia),
            'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
            'hora_fin': self.hora_fin.strftime('%H:%M') if self.hora_fin else None,
            'tipo_sesion': self.tipo_sesion,
            'conflicto': self.conflicto,
            'conflicto_con': self.conflicto_con or [],
            'notas': self.notas,
        }
        if expand:
            if self.materia:
                data['materia'] = {
                    'id': self.materia.id,
                    'clave': self.materia.clave,
                    'nombre': self.materia.nombre,
                    'nombre_corto': self.materia.nombre_corto or self.materia.nombre,
                    'tipo': self.materia.tipo,
                    'creditos': self.materia.creditos,
                }
            if self.salon:
                data['salon'] = {
                    'id': self.salon.id,
                    'codigo': self.salon.codigo,
                    'tipo': self.salon.tipo,
                }
            if self.profesor:
                data['profesor'] = {
                    'id': self.profesor.id,
                    'nombre_completo': self.profesor.nombre_completo,
                }
        return data


class PlantillaHorario(db.Model):
    __tablename__ = 'plantilla_horario'
    id = db.Column(db.Integer, primary_key=True)
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'))
    semestre = db.Column(db.Integer)
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodo_academico.id'))
    nombre = db.Column(db.String(100))
    bloques = db.Column(db.JSON)
    activa = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'carrera_id': self.carrera_id,
            'semestre': self.semestre,
            'periodo_id': self.periodo_id,
            'nombre': self.nombre,
            'bloques': self.bloques or [],
            'activa': self.activa,
        }
