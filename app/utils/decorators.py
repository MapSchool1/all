from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def roles_required(*roles):
    """Restringe el acceso a usuarios con uno de los roles indicados."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            uid = get_jwt_identity()
            try:
                user = User.query.get(int(uid)) if uid else None
            except (TypeError, ValueError):
                user = None
            if not user or user.is_deleted or user.estado != 'activo':
                return jsonify({'error': 'Cuenta inválida o suspendida',
                                'code': 'ACCOUNT_INVALID'}), 403
            if user.rol not in roles:
                return jsonify({'error': 'Permiso denegado',
                                'code': 'FORBIDDEN'}), 403
            request.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    """Devuelve el User autenticado en la request actual o None."""
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return None
    uid = get_jwt_identity()
    if not uid:
        return None
    try:
        user = User.query.get(int(uid))
    except (TypeError, ValueError):
        return None
    if not user or user.is_deleted:
        return None
    return user
