"""Audit log (lectura)."""
from datetime import datetime
from flask import Blueprint, jsonify, request

from app.models import AuditLog
from app.utils.decorators import roles_required
from app.utils.pagination import paginate

bp = Blueprint('audit_api', __name__)


@bp.get('')
@roles_required('rector', 'admin', 'director')
def list_audit():
    q = AuditLog.query
    for f in ('user_id',):
        v = request.args.get(f)
        if v:
            try:
                q = q.filter(getattr(AuditLog, f) == int(v))
            except ValueError:
                pass
    if request.args.get('accion'):
        q = q.filter_by(accion=request.args['accion'])
    if request.args.get('entidad'):
        q = q.filter_by(entidad=request.args['entidad'])
    for f, op in (('desde', '>='), ('hasta', '<=')):
        v = request.args.get(f)
        if v:
            try:
                d = datetime.fromisoformat(v)
                q = q.filter(AuditLog.created_at >= d if op == '>='
                             else AuditLog.created_at <= d)
            except ValueError:
                pass
    q = q.order_by(AuditLog.created_at.desc())
    items, meta = paginate(q)
    return jsonify({'data': [a.to_dict() for a in items], **meta})
