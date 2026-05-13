"""Notificaciones (lista, marcar leída, SSE stream)."""
import json
import time
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token

from app.extensions import db
from app.models import Notificacion, User
from app.utils.pagination import paginate

bp = Blueprint('notifications_api', __name__)


@bp.get('')
@jwt_required()
def list_notificaciones():
    uid = int(get_jwt_identity())
    q = Notificacion.query.filter_by(destinatario_id=uid)
    leida = request.args.get('leida')
    if leida is not None and leida != '':
        q = q.filter_by(leida=(leida.lower() == 'true'))
    if request.args.get('tipo'):
        q = q.filter_by(tipo=request.args['tipo'])
    q = q.order_by(Notificacion.created_at.desc())
    items, meta = paginate(q, default_per_page=20)
    no_leidas = Notificacion.query.filter_by(
        destinatario_id=uid, leida=False).count()
    return jsonify({'data': [n.to_dict() for n in items],
                    'no_leidas': no_leidas, **meta})


@bp.post('/<int:n_id>/leer')
@jwt_required()
def marcar_leida(n_id):
    uid = int(get_jwt_identity())
    n = Notificacion.query.get(n_id)
    if not n or n.destinatario_id != uid:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    if not n.leida:
        n.leida = True
        n.leida_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'notificacion': n.to_dict()})


@bp.post('/leer-todas')
@jwt_required()
def marcar_todas_leidas():
    uid = int(get_jwt_identity())
    n_count = Notificacion.query.filter_by(
        destinatario_id=uid, leida=False).update(
        {'leida': True, 'leida_at': datetime.utcnow()})
    db.session.commit()
    return jsonify({'leidas': n_count})


@bp.get('/stream')
def stream():
    """SSE — autentica vía query ?token=... porque EventSource no permite
    headers personalizados en el navegador."""
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token requerido en query string',
                        'code': 'MISSING_TOKEN'}), 401
    try:
        payload = decode_token(token)
        uid = int(payload['sub'])
    except Exception:
        return jsonify({'error': 'Token inválido',
                        'code': 'INVALID_TOKEN'}), 401
    if not User.query.get(uid):
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404

    @stream_with_context
    def generate():
        last_id = 0
        # Enviar el último estado al conectar
        ult = (Notificacion.query.filter_by(destinatario_id=uid, leida=False)
               .order_by(Notificacion.id.desc()).first())
        if ult:
            last_id = ult.id
        yield f'event: ping\ndata: {{"connected": true}}\n\n'
        for _ in range(360):  # ~1h máx (10s * 360)
            time.sleep(10)
            nuevas = (Notificacion.query
                      .filter(Notificacion.destinatario_id == uid,
                              Notificacion.id > last_id)
                      .order_by(Notificacion.id).all())
            for n in nuevas:
                yield f'data: {json.dumps(n.to_dict())}\n\n'
                last_id = n.id
            yield 'event: ping\ndata: {}\n\n'

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache',
                             'X-Accel-Buffering': 'no'})
