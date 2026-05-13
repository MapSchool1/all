"""Edificios, salones y disponibilidad en tiempo real."""
from datetime import datetime, time
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Edificio, Salon, Bloque, Horario, PeriodoAcademico
from app.utils.decorators import roles_required
from app.utils.conflicts import salon_disponible

bp = Blueprint('campus_api', __name__)

DIA_BY_WEEKDAY = {0: 'lun', 1: 'mar', 2: 'mie', 3: 'jue', 4: 'vie', 5: 'sab'}


def _periodo_activo_id():
    p = PeriodoAcademico.query.filter_by(activo=True).first()
    return p.id if p else None


# =============== EDIFICIOS ===============

@bp.get('/edificios')
def list_edificios():
    q = Edificio.query.filter_by(activo=True)
    if request.args.get('plantel_id'):
        try:
            q = q.filter_by(plantel_id=int(request.args['plantel_id']))
        except ValueError:
            pass
    items = q.order_by(Edificio.clave).all()
    return jsonify({'data': [e.to_dict() for e in items]})


@bp.get('/edificios/<int:e_id>')
def get_edificio(e_id):
    e = Edificio.query.get(e_id)
    if not e:
        return jsonify({'error': 'Edificio no encontrado',
                        'code': 'NOT_FOUND'}), 404
    salones = [s.to_dict(include_edificio=False)
               for s in e.salones if s.activo and not s.deleted_at]
    return jsonify({'edificio': e.to_dict(), 'salones': salones})


@bp.post('/edificios')
@roles_required('admin', 'director')
def create_edificio():
    data = request.get_json(silent=True) or {}
    if not data.get('clave') or not data.get('nombre'):
        return jsonify({'error': 'Clave y nombre son obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    if Edificio.query.filter_by(clave=data['clave']).first():
        return jsonify({'error': 'Clave duplicada',
                        'code': 'CLAVE_DUPLICATE'}), 409
    e = Edificio(**{k: data.get(k) for k in (
        'clave', 'nombre', 'descripcion', 'plantel_id',
        'coordenadas_x', 'coordenadas_y', 'ancho_mapa', 'alto_mapa',
        'color_mapa', 'activo') if k in data})
    db.session.add(e)
    db.session.commit()
    return jsonify({'edificio': e.to_dict()}), 201


@bp.put('/edificios/<int:e_id>')
@roles_required('admin', 'director')
def update_edificio(e_id):
    e = Edificio.query.get(e_id)
    if not e:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('nombre', 'descripcion', 'coordenadas_x', 'coordenadas_y',
              'ancho_mapa', 'alto_mapa', 'color_mapa', 'activo'):
        if f in data:
            setattr(e, f, data[f])
    db.session.commit()
    return jsonify({'edificio': e.to_dict()})


@bp.delete('/edificios/<int:e_id>')
@roles_required('admin')
def delete_edificio(e_id):
    e = Edificio.query.get(e_id)
    if not e:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    e.activo = False
    db.session.commit()
    return jsonify({'message': 'Edificio desactivado'})


# =============== SALONES ===============

def _salon_disponible_ahora(salon: Salon, periodo_id):
    if not periodo_id:
        return True
    now = datetime.now()
    dia = DIA_BY_WEEKDAY.get(now.weekday())
    if not dia:
        return True
    hora_actual = now.time()
    bloques = (Bloque.query.join(Horario, Horario.id == Bloque.horario_id)
               .filter(Bloque.salon_id == salon.id,
                       Bloque.dia == dia,
                       Horario.periodo_id == periodo_id,
                       Horario.estado == 'publicado',
                       Horario.deleted_at.is_(None))
               .all())
    for b in bloques:
        if b.hora_inicio <= hora_actual < b.hora_fin:
            return False
    return True


@bp.get('/salones')
def list_salones():
    q = Salon.query.filter(Salon.deleted_at.is_(None))
    if request.args.get('edificio_id'):
        try:
            q = q.filter_by(edificio_id=int(request.args['edificio_id']))
        except ValueError:
            pass
    if request.args.get('tipo'):
        q = q.filter_by(tipo=request.args['tipo'])
    if request.args.get('capacidad_min'):
        try:
            q = q.filter(Salon.capacidad >= int(request.args['capacidad_min']))
        except ValueError:
            pass
    activo = request.args.get('activo', 'true').lower() == 'true'
    q = q.filter_by(activo=activo)
    salones = q.order_by(Salon.codigo).all()
    periodo_id = _periodo_activo_id()
    out = []
    for s in salones:
        d = s.to_dict()
        d['disponible_ahora'] = _salon_disponible_ahora(s, periodo_id)
        out.append(d)
    if request.args.get('disponible_ahora') in ('true', '1'):
        out = [s for s in out if s['disponible_ahora']]
    return jsonify({'data': out, 'total': len(out)})


@bp.get('/salones/<int:s_id>')
def get_salon(s_id):
    s = Salon.query.get(s_id)
    if not s or s.deleted_at:
        return jsonify({'error': 'Salón no encontrado',
                        'code': 'NOT_FOUND'}), 404
    return jsonify(_salon_full(s))


@bp.get('/salones/codigo/<string:codigo>')
def get_salon_codigo(codigo):
    s = Salon.query.filter_by(codigo=codigo).first()
    if not s or s.deleted_at:
        return jsonify({'error': 'Salón no encontrado',
                        'code': 'NOT_FOUND'}), 404
    return jsonify(_salon_full(s))


def _salon_full(salon: Salon):
    periodo_id = _periodo_activo_id()
    disponibilidad = {d: [] for d in ('lun', 'mar', 'mie', 'jue', 'vie', 'sab')}
    if periodo_id:
        bloques = (Bloque.query.join(Horario, Horario.id == Bloque.horario_id)
                   .filter(Bloque.salon_id == salon.id,
                           Horario.periodo_id == periodo_id,
                           Horario.estado == 'publicado',
                           Horario.deleted_at.is_(None))
                   .all())
        for b in bloques:
            disponibilidad[b.dia].append({
                'hora_inicio': b.hora_inicio.strftime('%H:%M'),
                'hora_fin': b.hora_fin.strftime('%H:%M'),
                'ocupado': True,
                'materia': b.materia.nombre if b.materia else None,
                'grupo': None,
                'profesor': b.profesor.nombre_completo if b.profesor else None,
            })
        for d in disponibilidad:
            disponibilidad[d].sort(key=lambda x: x['hora_inicio'])
    return {
        'salon': salon.to_dict(),
        'disponibilidad_semana': disponibilidad,
        'disponible_ahora': _salon_disponible_ahora(salon, periodo_id),
    }


@bp.get('/salones/<int:s_id>/disponibilidad')
def salon_disp_check(s_id):
    s = Salon.query.get(s_id)
    if not s:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    dia = request.args.get('dia')
    hi = request.args.get('hora_inicio')
    hf = request.args.get('hora_fin')
    periodo_id = request.args.get('periodo_id') or _periodo_activo_id()
    if not (dia and hi and hf and periodo_id):
        return jsonify({'error': 'Parámetros requeridos: dia, hora_inicio, '
                        'hora_fin, periodo_id', 'code': 'MISSING_PARAMS'}), 422
    try:
        h_i = time.fromisoformat(hi)
        h_f = time.fromisoformat(hf)
        periodo_id = int(periodo_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato inválido',
                        'code': 'INVALID_FORMAT'}), 422
    libre, conflicto = salon_disponible(s.id, dia, h_i, h_f, periodo_id)
    return jsonify({
        'disponible': libre,
        'conflictos': [conflicto.to_dict()] if conflicto else [],
    })


@bp.get('/salones/buscar')
@jwt_required()
def buscar_salones():
    dia = request.args.get('dia')
    hi = request.args.get('hora_inicio')
    hf = request.args.get('hora_fin')
    if not (dia and hi and hf):
        return jsonify({'error': 'Parámetros requeridos: dia, hora_inicio, '
                        'hora_fin', 'code': 'MISSING_PARAMS'}), 422
    try:
        h_i = time.fromisoformat(hi)
        h_f = time.fromisoformat(hf)
    except ValueError:
        return jsonify({'error': 'Formato inválido',
                        'code': 'INVALID_FORMAT'}), 422
    q = Salon.query.filter(Salon.deleted_at.is_(None), Salon.activo.is_(True))
    if request.args.get('tipo'):
        q = q.filter_by(tipo=request.args['tipo'])
    if request.args.get('capacidad_min'):
        try:
            q = q.filter(Salon.capacidad >= int(request.args['capacidad_min']))
        except ValueError:
            pass
    periodo_id = _periodo_activo_id()
    disponibles, ocupados = [], []
    for s in q.all():
        libre, _ = salon_disponible(s.id, dia, h_i, h_f, periodo_id)
        (disponibles if libre else ocupados).append(s.to_dict())
    return jsonify({'disponibles': disponibles, 'ocupados': ocupados})


@bp.post('/salones')
@roles_required('coordinador', 'admin', 'director')
def create_salon():
    data = request.get_json(silent=True) or {}
    required = ['edificio_id', 'codigo', 'tipo', 'capacidad']
    missing = [f for f in required if not data.get(f) and data.get(f) != 0]
    if missing:
        return jsonify({'error': 'Faltan campos',
                        'code': 'MISSING_FIELDS', 'fields': missing}), 422
    if Salon.query.filter_by(codigo=data['codigo']).first():
        return jsonify({'error': 'Código duplicado',
                        'code': 'CODIGO_DUPLICATE', 'field': 'codigo'}), 409
    s = Salon(**{k: data.get(k) for k in (
        'edificio_id', 'codigo', 'nombre', 'tipo', 'capacidad', 'piso',
        'descripcion', 'equipamiento', 'coord_x', 'coord_y', 'activo')
              if k in data})
    db.session.add(s)
    db.session.commit()
    return jsonify({'salon': s.to_dict()}), 201


@bp.put('/salones/<int:s_id>')
@roles_required('coordinador', 'admin', 'director')
def update_salon(s_id):
    s = Salon.query.get(s_id)
    if not s:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('nombre', 'tipo', 'capacidad', 'piso', 'descripcion',
              'equipamiento', 'coord_x', 'coord_y', 'activo', 'edificio_id'):
        if f in data:
            setattr(s, f, data[f])
    db.session.commit()
    return jsonify({'salon': s.to_dict()})


@bp.delete('/salones/<int:s_id>')
@roles_required('admin')
def delete_salon(s_id):
    s = Salon.query.get(s_id)
    if not s:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    s.activo = False
    db.session.commit()
    return jsonify({'message': 'Salón desactivado'})
