"""Anuncios visibles para audiencias."""
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Anuncio, User
from app.utils.decorators import roles_required

bp = Blueprint('anuncios_api', __name__)


def _audience_for(user: User):
    aud = ['todos']
    if user.rol == 'estudiante':
        aud.append('estudiantes')
    elif user.rol == 'profesor':
        aud.append('profesores')
    elif user.rol in ('admin', 'director', 'coordinador', 'rector'):
        aud.extend(['admin', 'profesores'])
    return aud


@bp.get('')
@jwt_required()
def list_anuncios():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    aud = _audience_for(user)
    now = datetime.utcnow()
    q = Anuncio.query.filter(
        Anuncio.publicado.is_(True),
        Anuncio.audiencia.in_(aud),
    )
    items = q.order_by(Anuncio.fijado.desc(),
                       Anuncio.created_at.desc()).all()
    visible = [a for a in items if not a.expira_at or a.expira_at >= now]
    fijados = [a.to_dict() for a in visible if a.fijado]
    return jsonify({'data': [a.to_dict() for a in visible],
                    'fijados': fijados})


@bp.post('')
@roles_required('coordinador', 'admin', 'director', 'rector', 'profesor')
def create_anuncio():
    data = request.get_json(silent=True) or {}
    if not data.get('titulo'):
        return jsonify({'error': 'Título requerido',
                        'code': 'MISSING_FIELDS'}), 422
    uid = int(get_jwt_identity())
    a = Anuncio(
        autor_id=uid,
        plantel_id=data.get('plantel_id'),
        titulo=data['titulo'],
        cuerpo=data.get('cuerpo'),
        audiencia=data.get('audiencia', 'todos'),
        carrera_id=data.get('carrera_id'),
        fijado=data.get('fijado', False),
        publicado=data.get('publicado', False),
        publicado_at=datetime.utcnow() if data.get('publicado') else None,
        expira_at=(datetime.fromisoformat(data['expira_at'])
                   if data.get('expira_at') else None),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({'anuncio': a.to_dict()}), 201


@bp.put('/<int:a_id>')
@jwt_required()
def update_anuncio(a_id):
    a = Anuncio.query.get(a_id)
    if not a:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if a.autor_id != uid and user.rol not in (
            'admin', 'director', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    for f in ('titulo', 'cuerpo', 'audiencia', 'carrera_id',
              'fijado', 'publicado'):
        if f in data:
            setattr(a, f, data[f])
    if data.get('publicado') and not a.publicado_at:
        a.publicado_at = datetime.utcnow()
    if 'expira_at' in data:
        a.expira_at = (datetime.fromisoformat(data['expira_at'])
                       if data['expira_at'] else None)
    db.session.commit()
    return jsonify({'anuncio': a.to_dict()})


@bp.delete('/<int:a_id>')
@jwt_required()
def delete_anuncio(a_id):
    a = Anuncio.query.get(a_id)
    if not a:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if a.autor_id != uid and user.rol not in (
            'admin', 'director', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    db.session.delete(a)
    db.session.commit()
    return jsonify({'message': 'Anuncio eliminado'})
