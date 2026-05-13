from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


ESTADOS_TRAMITE = ('recibido', 'en_proceso', 'pendiente_pago',
                   'listo', 'entregado', 'rechazado')


class TipoTramite(db.Model):
    __tablename__ = 'tipo_tramite'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    requiere_documentos = db.Column(db.JSON)
    costo = db.Column(db.Numeric(10, 2), default=0)
    tiempo_estimado_dias = db.Column(db.Integer, default=3)
    activo = db.Column(db.Boolean, default=True)

    tramites = db.relationship('Tramite', backref='tipo_tramite', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'requiere_documentos': self.requiere_documentos or [],
            'costo': float(self.costo) if self.costo is not None else 0,
            'tiempo_estimado_dias': self.tiempo_estimado_dias,
            'activo': self.activo,
        }


class Tramite(db.Model):
    __tablename__ = 'tramite'
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True, nullable=False, index=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                               nullable=False, index=True)
    tipo_tramite_id = db.Column(db.Integer, db.ForeignKey('tipo_tramite.id'),
                                nullable=False)
    estado = db.Column(db.Enum(*ESTADOS_TRAMITE, name='estado_tramite_enum'),
                       default='recibido', index=True)
    descripcion = db.Column(db.Text)
    documentos = db.Column(db.JSON)
    resultado_url = db.Column(db.String(500))
    atendido_por = db.Column(db.Integer, db.ForeignKey('user.id'))
    notas_admin = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    entregado_at = db.Column(db.DateTime)

    solicitante = db.relationship('User', foreign_keys=[solicitante_id], lazy='select')
    seguimiento = db.relationship('SeguimientoTramite', backref='tramite',
                                  cascade='all, delete-orphan', lazy='select')

    def to_dict(self, expand=True):
        data = {
            'id': self.id,
            'folio': self.folio,
            'solicitante_id': self.solicitante_id,
            'tipo_tramite_id': self.tipo_tramite_id,
            'estado': self.estado,
            'descripcion': self.descripcion,
            'documentos': self.documentos or [],
            'resultado_url': self.resultado_url,
            'notas_admin': self.notas_admin,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
            'entregado_at': self.entregado_at.isoformat() + 'Z' if self.entregado_at else None,
        }
        if expand:
            if self.tipo_tramite:
                data['tipo'] = {
                    'id': self.tipo_tramite.id,
                    'nombre': self.tipo_tramite.nombre,
                    'tiempo_estimado_dias': self.tipo_tramite.tiempo_estimado_dias,
                }
            if self.solicitante:
                data['solicitante'] = {
                    'id': self.solicitante.id,
                    'nombre_completo': self.solicitante.nombre_completo,
                    'email': self.solicitante.email,
                    'expediente': self.solicitante.expediente,
                }
        return data


class SeguimientoTramite(db.Model):
    __tablename__ = 'seguimiento_tramite'
    id = db.Column(db.Integer, primary_key=True)
    tramite_id = db.Column(db.Integer, db.ForeignKey('tramite.id'),
                           nullable=False, index=True)
    estado_anterior = db.Column(db.String(30))
    estado_nuevo = db.Column(db.String(30))
    comentario = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=utcnow)

    usuario = db.relationship('User', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'estado_anterior': self.estado_anterior,
            'estado_nuevo': self.estado_nuevo,
            'comentario': self.comentario,
            'usuario': self.usuario.nombre_completo if self.usuario else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
