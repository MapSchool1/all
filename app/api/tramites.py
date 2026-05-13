"""Trámites administrativos."""
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Tramite, TipoTramite, SeguimientoTramite, User
from app.utils.decorators import roles_required
from app.utils.pagination import paginate
from app.utils.notify import notify

bp = Blueprint('tramites_api', __name__)


@bp.get('/tipos')
def list_tipos():
    items = TipoTramite.query.filter_by(activo=True).order_by(
        TipoTramite.nombre).all()
    return jsonify({'data': [t.to_dict() for t in items]})


@bp.post('/tipos')
@roles_required('admin')
def create_tipo():
    data = request.get_json(silent=True) or {}
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre requerido',
                        'code': 'MISSING_FIELDS'}), 422
    t = TipoTramite(
        nombre=data['nombre'],
        descripcion=data.get('descripcion'),
        requiere_documentos=data.get('requiere_documentos', []),
        costo=data.get('costo', 0),
        tiempo_estimado_dias=data.get('tiempo_estimado_dias', 3),
        activo=data.get('activo', True),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'tipo': t.to_dict()}), 201


@bp.get('')
@jwt_required()
def list_tramites():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    is_admin = user.rol in ('admin', 'coordinador', 'director')
    q = Tramite.query
    if not is_admin:
        q = q.filter_by(solicitante_id=uid)
    if request.args.get('estado'):
        q = q.filter_by(estado=request.args['estado'])
    if request.args.get('tipo_id'):
        try:
            q = q.filter_by(tipo_tramite_id=int(request.args['tipo_id']))
        except ValueError:
            pass
    q = q.order_by(Tramite.created_at.desc())
    items, meta = paginate(q)
    return jsonify({'data': [t.to_dict() for t in items], **meta})


def _next_folio():
    year = datetime.utcnow().year
    prefix = f'TRM-{year}-'
    last = (Tramite.query.filter(Tramite.folio.like(f'{prefix}%'))
            .order_by(Tramite.id.desc()).first())
    if last and last.folio.startswith(prefix):
        try:
            n = int(last.folio.split('-')[-1]) + 1
        except (IndexError, ValueError):
            n = 1
    else:
        n = 1
    return f'{prefix}{n:05d}'


@bp.post('')
@jwt_required()
def create_tramite():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    tipo = TipoTramite.query.get(data.get('tipo_tramite_id'))
    if not tipo or not tipo.activo:
        return jsonify({'error': 'Tipo de trámite inválido',
                        'code': 'INVALID_TIPO'}), 422
    folio = _next_folio()
    t = Tramite(
        folio=folio,
        solicitante_id=uid,
        tipo_tramite_id=tipo.id,
        descripcion=data.get('descripcion'),
        documentos=data.get('documentos', []),
    )
    db.session.add(t)
    db.session.flush()
    db.session.add(SeguimientoTramite(
        tramite_id=t.id, estado_anterior=None,
        estado_nuevo='recibido',
        comentario='Trámite recibido',
        usuario_id=uid))

    admins = User.query.filter(User.rol.in_(('admin', 'coordinador')),
                               User.estado == 'activo',
                               User.deleted_at.is_(None)).all()
    for a in admins:
        notify(a.id, 'tramite',
               f'Nuevo trámite {folio}',
               f'{tipo.nombre} solicitado.',
               accion_url=f'/admin/tramites?folio={folio}',
               commit=False)
    db.session.commit()
    return jsonify({'tramite': t.to_dict()}), 201


@bp.get('/<int:t_id>')
@jwt_required()
def get_tramite(t_id):
    t = Tramite.query.get(t_id)
    if not t:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if t.solicitante_id != uid and user.rol not in (
            'admin', 'coordinador', 'director'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    seg = SeguimientoTramite.query.filter_by(tramite_id=t_id).order_by(
        SeguimientoTramite.created_at).all()
    return jsonify({'tramite': t.to_dict(),
                    'seguimiento': [s.to_dict() for s in seg]})


@bp.put('/<int:t_id>/estado')
@roles_required('admin', 'coordinador', 'director')
def update_estado(t_id):
    t = Tramite.query.get(t_id)
    if not t:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    nuevo = data.get('estado')
    if nuevo not in ('recibido', 'en_proceso', 'pendiente_pago',
                     'listo', 'entregado', 'rechazado'):
        return jsonify({'error': 'Estado inválido',
                        'code': 'INVALID_ESTADO'}), 422
    anterior = t.estado
    t.estado = nuevo
    t.atendido_por = int(get_jwt_identity())
    if nuevo == 'entregado':
        t.entregado_at = datetime.utcnow()
    db.session.add(SeguimientoTramite(
        tramite_id=t.id, estado_anterior=anterior,
        estado_nuevo=nuevo, comentario=data.get('comentario'),
        usuario_id=t.atendido_por))
    notify(t.solicitante_id, 'tramite',
           f'Trámite {t.folio} actualizado',
           f'Tu trámite cambió a estado: {nuevo.replace("_", " ")}.',
           accion_url=f'/tramites/{t.id}', commit=False)
    db.session.commit()
    return jsonify({'tramite': t.to_dict()})
