from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


TIPOS_NOTIF = ('horario', 'calificacion', 'tramite', 'anuncio',
               'sistema', 'conflicto', 'asistencia')
AUDIENCIAS_ANUNCIO = ('todos', 'estudiantes', 'profesores', 'admin')


class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    id = db.Column(db.Integer, primary_key=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                                nullable=False, index=True)
    tipo = db.Column(db.Enum(*TIPOS_NOTIF, name='tipo_notif_enum'))
    titulo = db.Column(db.String(200), nullable=False)
    cuerpo = db.Column(db.Text)
    leida = db.Column(db.Boolean, default=False, index=True)
    accion_url = db.Column(db.String(500))
    extra = db.Column('metadata', db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    leida_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'destinatario_id': self.destinatario_id,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'cuerpo': self.cuerpo,
            'leida': self.leida,
            'accion_url': self.accion_url,
            'metadata': self.extra,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'leida_at': self.leida_at.isoformat() + 'Z' if self.leida_at else None,
        }


class Anuncio(db.Model):
    __tablename__ = 'anuncio'
    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'))
    titulo = db.Column(db.String(200), nullable=False)
    cuerpo = db.Column(db.Text)
    audiencia = db.Column(db.Enum(*AUDIENCIAS_ANUNCIO, name='audiencia_anuncio_enum'),
                          default='todos')
    carrera_id = db.Column(db.Integer, db.ForeignKey('carrera.id'), nullable=True)
    fijado = db.Column(db.Boolean, default=False, index=True)
    publicado = db.Column(db.Boolean, default=False, index=True)
    publicado_at = db.Column(db.DateTime)
    expira_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)

    autor = db.relationship('User', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'autor_id': self.autor_id,
            'autor': self.autor.nombre_completo if self.autor else None,
            'plantel_id': self.plantel_id,
            'titulo': self.titulo,
            'cuerpo': self.cuerpo,
            'audiencia': self.audiencia,
            'carrera_id': self.carrera_id,
            'fijado': self.fijado,
            'publicado': self.publicado,
            'publicado_at': self.publicado_at.isoformat() + 'Z' if self.publicado_at else None,
            'expira_at': self.expira_at.isoformat() + 'Z' if self.expira_at else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
