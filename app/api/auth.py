"""Endpoints de autenticación y gestión de sesión."""
from datetime import datetime, timedelta
import re
import secrets

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt, get_jwt_identity, decode_token,
)

from app.extensions import db, limiter
from app.models import User, RefreshToken

bp = Blueprint('auth_api', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PASSWORD_MIN = 8


def _validate_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email))


def _validate_password(password: str):
    if not password or len(password) < PASSWORD_MIN:
        return f'La contraseña debe tener al menos {PASSWORD_MIN} caracteres'
    if not any(c.isalpha() for c in password):
        return 'La contraseña debe incluir al menos una letra'
    if not any(c.isdigit() for c in password):
        return 'La contraseña debe incluir al menos un número'
    return None


def _save_refresh(user_id, jti, expires_in_seconds):
    rt = RefreshToken(
        user_id=user_id,
        token_jti=jti,
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in_seconds),
    )
    db.session.add(rt)
    return rt


def _issue_tokens(user: User):
    access = create_access_token(identity=str(user.id),
                                 additional_claims={'rol': user.rol,
                                                    'email': user.email})
    refresh = create_refresh_token(identity=str(user.id),
                                   additional_claims={'rol': user.rol})
    payload = decode_token(refresh)
    expires_in = current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()
    _save_refresh(user.id, payload['jti'], int(expires_in))
    return access, refresh


@bp.post('/login')
@limiter.limit('10 per minute')
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'Correo y contraseña son obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    user = User.query.filter_by(email=email).first()
    if not user or user.is_deleted:
        return jsonify({'error': 'Credenciales inválidas',
                        'code': 'INVALID_CREDENTIALS'}), 401
    if user.estado in ('suspendido', 'inactivo', 'eliminado'):
        return jsonify({'error': 'Tu cuenta no está activa. Contacta a soporte.',
                        'code': 'ACCOUNT_INACTIVE'}), 403
    if not user.check_password(password):
        user.intentos_fallidos = (user.intentos_fallidos or 0) + 1
        if user.intentos_fallidos >= 8:
            user.estado = 'suspendido'
        db.session.commit()
        return jsonify({'error': 'Credenciales inválidas',
                        'code': 'INVALID_CREDENTIALS'}), 401
    user.intentos_fallidos = 0
    user.ultimo_acceso = datetime.utcnow()
    access, refresh = _issue_tokens(user)
    db.session.commit()
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
        'user': user.to_dict(),
    })


@bp.post('/register')
@limiter.limit('20 per hour')
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    nombre = (data.get('nombre') or '').strip()
    apellido_p = (data.get('apellido_p') or '').strip()
    apellido_m = (data.get('apellido_m') or '').strip() or None
    password = data.get('password') or ''
    rol = data.get('rol') or 'estudiante'
    plantel_id = data.get('plantel_id')
    carrera_id = data.get('carrera_id')

    errors = {}
    if not _validate_email(email):
        errors['email'] = 'Correo no válido'
    if not nombre:
        errors['nombre'] = 'El nombre es obligatorio'
    if not apellido_p:
        errors['apellido_p'] = 'El apellido paterno es obligatorio'
    pw_error = _validate_password(password)
    if pw_error:
        errors['password'] = pw_error
    if rol not in ('estudiante', 'aspirante', 'invitado', 'profesor'):
        errors['rol'] = 'Rol no permitido en registro abierto'
    if errors:
        return jsonify({'error': 'Datos inválidos', 'code': 'VALIDATION_ERROR',
                        'fields': errors}), 422
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Ya existe una cuenta con ese correo',
                        'code': 'EMAIL_DUPLICATE', 'field': 'email'}), 409

    user = User(email=email, nombre=nombre, apellido_p=apellido_p,
                apellido_m=apellido_m, rol=rol,
                plantel_id=plantel_id, carrera_id=carrera_id,
                estado='activo')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    access, refresh = _issue_tokens(user)
    user.ultimo_acceso = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
        'user': user.to_dict(),
    }), 201


@bp.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    uid = get_jwt_identity()
    user = User.query.get(int(uid)) if uid else None
    if not user or user.is_deleted or user.estado != 'activo':
        return jsonify({'error': 'Cuenta no disponible',
                        'code': 'ACCOUNT_INVALID'}), 403
    # Rotación: revocar el refresh actual y emitir uno nuevo
    jti = get_jwt().get('jti')
    if jti:
        rt = RefreshToken.query.filter_by(token_jti=jti).first()
        if rt:
            rt.revoked = True
    access, new_refresh = _issue_tokens(user)
    db.session.commit()
    return jsonify({
        'access_token': access,
        'refresh_token': new_refresh,
        'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
    })


@bp.post('/logout')
@jwt_required()
def logout():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get('refresh_token')
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get('jti')
            rt = RefreshToken.query.filter_by(token_jti=jti).first()
            if rt:
                rt.revoked = True
        except Exception:
            pass
    db.session.commit()
    return jsonify({'message': 'Sesión cerrada'})


@bp.post('/logout-all')
@jwt_required()
def logout_all():
    uid = int(get_jwt_identity())
    RefreshToken.query.filter_by(user_id=uid, revoked=False).update({'revoked': True})
    db.session.commit()
    return jsonify({'message': 'Todas las sesiones se han cerrado'})


@bp.get('/me')
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    return jsonify({'user': user.to_dict()})


@bp.post('/password/change')
@jwt_required()
def password_change():
    data = request.get_json(silent=True) or {}
    actual = data.get('password_actual') or ''
    nueva = data.get('password_nuevo') or ''
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    if not user.check_password(actual):
        return jsonify({'error': 'Contraseña actual incorrecta',
                        'code': 'INVALID_PASSWORD',
                        'field': 'password_actual'}), 422
    err = _validate_password(nueva)
    if err:
        return jsonify({'error': err, 'code': 'INVALID_PASSWORD',
                        'field': 'password_nuevo'}), 422
    user.set_password(nueva)
    RefreshToken.query.filter_by(user_id=uid, revoked=False).update({'revoked': True})
    db.session.commit()
    return jsonify({'message': 'Contraseña actualizada. Vuelve a iniciar sesión.'})


@bp.post('/password/reset-request')
@limiter.limit('5 per hour')
def password_reset_request():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first()
    msg = {'message': 'Si la cuenta existe, recibirás un correo con instrucciones.'}
    if not user or user.is_deleted:
        return jsonify(msg)
    token = secrets.token_urlsafe(32)
    user.password_hash = user.password_hash  # marcar updated_at
    user._reset_token = token  # type: ignore[attr-defined]
    if current_app.debug:
        current_app.logger.warning('Reset token (dev) para %s: %s', email, token)
    return jsonify(msg)
