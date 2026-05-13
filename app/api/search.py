"""Búsqueda global."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from app.models import User, Materia, Salon, Tramite

bp = Blueprint('search_api', __name__)


@bp.get('')
@jwt_required()
def buscar():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'usuarios': [], 'materias': [], 'salones': [],
                        'tramites': [], 'total': 0})
    tipos = (request.args.get('tipos') or
             'usuarios,materias,salones,tramites').split(',')
    like = f'%{q}%'
    user = User.query.get(int(get_jwt_identity()))
    is_admin = user.rol in ('admin', 'director', 'coordinador', 'rector')
    out = {'usuarios': [], 'materias': [], 'salones': [], 'tramites': []}

    if 'usuarios' in tipos and is_admin:
        usuarios = User.query.filter(
            User.deleted_at.is_(None),
            or_(User.nombre.ilike(like), User.apellido_p.ilike(like),
                User.email.ilike(like), User.expediente.ilike(like))
        ).limit(8).all()
        out['usuarios'] = [u.to_dict() for u in usuarios]
    if 'materias' in tipos:
        materias = Materia.query.filter(
            Materia.deleted_at.is_(None),
            or_(Materia.nombre.ilike(like), Materia.clave.ilike(like))
        ).limit(8).all()
        out['materias'] = [m.to_dict() for m in materias]
    if 'salones' in tipos:
        salones = Salon.query.filter(
            Salon.deleted_at.is_(None),
            or_(Salon.codigo.ilike(like), Salon.nombre.ilike(like))
        ).limit(8).all()
        out['salones'] = [s.to_dict() for s in salones]
    if 'tramites' in tipos:
        q_tr = Tramite.query.filter(Tramite.folio.ilike(like))
        if not is_admin:
            q_tr = q_tr.filter_by(solicitante_id=user.id)
        out['tramites'] = [t.to_dict() for t in q_tr.limit(8).all()]
    out['total'] = sum(len(v) for v in out.values())
    return jsonify(out)
