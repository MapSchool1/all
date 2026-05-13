from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


TIPOS_SALON = ('aula', 'laboratorio', 'auditorio', 'sala_computo',
               'sala_idiomas', 'otro')
TIPOS_POI = ('edificio', 'bano', 'cafeteria', 'biblioteca',
             'enfermeria', 'estacionamiento', 'canchas', 'otro')


class Edificio(db.Model):
    __tablename__ = 'edificio'
    id = db.Column(db.Integer, primary_key=True)
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'))
    nombre = db.Column(db.String(100), nullable=False)
    clave = db.Column(db.String(10), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    coordenadas_x = db.Column(db.Float, default=0)
    coordenadas_y = db.Column(db.Float, default=0)
    ancho_mapa = db.Column(db.Float, default=180)
    alto_mapa = db.Column(db.Float, default=130)
    color_mapa = db.Column(db.String(7), default='#172846')
    activo = db.Column(db.Boolean, default=True)

    salones = db.relationship('Salon', backref='edificio', lazy='select')

    def to_dict(self, include_count=True):
        data = {
            'id': self.id,
            'plantel_id': self.plantel_id,
            'nombre': self.nombre,
            'clave': self.clave,
            'descripcion': self.descripcion,
            'coordenadas_x': self.coordenadas_x,
            'coordenadas_y': self.coordenadas_y,
            'ancho_mapa': self.ancho_mapa,
            'alto_mapa': self.alto_mapa,
            'color_mapa': self.color_mapa,
            'activo': self.activo,
        }
        if include_count:
            data['total_salones'] = sum(1 for s in self.salones if s.activo)
        return data


class Salon(db.Model):
    __tablename__ = 'salon'
    id = db.Column(db.Integer, primary_key=True)
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificio.id'),
                            nullable=False, index=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(100))
    tipo = db.Column(db.Enum(*TIPOS_SALON, name='tipo_salon_enum'))
    capacidad = db.Column(db.Integer, nullable=False, default=30)
    piso = db.Column(db.Integer, default=1)
    descripcion = db.Column(db.Text)
    equipamiento = db.Column(db.JSON)
    coord_x = db.Column(db.Float, default=0)
    coord_y = db.Column(db.Float, default=0)
    activo = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    bloques = db.relationship('Bloque', backref='salon', lazy='select')

    def to_dict(self, include_edificio=True):
        data = {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre or self.codigo,
            'tipo': self.tipo,
            'capacidad': self.capacidad,
            'piso': self.piso,
            'descripcion': self.descripcion,
            'equipamiento': self.equipamiento or [],
            'coord_x': self.coord_x,
            'coord_y': self.coord_y,
            'activo': self.activo,
            'edificio_id': self.edificio_id,
        }
        if include_edificio and self.edificio:
            data['edificio'] = {
                'id': self.edificio.id,
                'clave': self.edificio.clave,
                'nombre': self.edificio.nombre,
            }
        return data


class PuntoInteres(db.Model):
    __tablename__ = 'punto_interes'
    id = db.Column(db.Integer, primary_key=True)
    plantel_id = db.Column(db.Integer, db.ForeignKey('plantel.id'))
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.Enum(*TIPOS_POI, name='tipo_poi_enum'))
    descripcion = db.Column(db.Text)
    coord_x = db.Column(db.Float, default=0)
    coord_y = db.Column(db.Float, default=0)
    icono = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'descripcion': self.descripcion,
            'coord_x': self.coord_x,
            'coord_y': self.coord_y,
            'icono': self.icono,
            'activo': self.activo,
        }
