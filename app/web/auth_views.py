"""Vistas web de autenticación (login, registro, logout)."""
from datetime import datetime, timedelta
import secrets
from flask import (Blueprint, render_template, redirect, url_for, request,
                   session, jsonify, current_app)
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    decode_token,
)

from app.extensions import db, limiter
from app.models import Plantel, Carrera, User, RefreshToken

bp = Blueprint('web_auth', __name__)


@bp.get('/login')
def login():
    if session.get('user_id'):
        return _redirect_by_role(session.get('user_rol'))
    return render_template('auth/login.html')


def _issue_web_session(user, response):
    """Establece sesión Flask + cookies httpOnly con JWT. Devuelve response."""
    access = create_access_token(identity=str(user.id),
        additional_claims={'rol': user.rol, 'email': user.email})
    refresh = create_refresh_token(identity=str(user.id),
        additional_claims={'rol': user.rol})
    payload = decode_token(refresh)
    expires = current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()
    db.session.add(RefreshToken(
        user_id=user.id, token_jti=payload['jti'],
        expires_at=datetime.utcnow() + timedelta(seconds=int(expires)),
    ))
    db.session.commit()
    set_access_cookies(response, access)
    set_refresh_cookies(response, refresh)
    return response


@bp.post('/web-login')
@limiter.limit('10 per minute')
def login_post():
    """Login server-side: sesión Flask + cookies httpOnly con JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'Correo y contraseña son obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    user = User.query.filter_by(email=email).first()
    if not user or user.is_deleted or not user.check_password(password):
        return jsonify({'error': 'Credenciales inválidas',
                        'code': 'INVALID_CREDENTIALS'}), 401
    if user.estado != 'activo':
        return jsonify({'error': 'Tu cuenta no está activa. Contacta a soporte.',
                        'code': 'ACCOUNT_INACTIVE'}), 403
    user.ultimo_acceso = datetime.utcnow()
    user.intentos_fallidos = 0
    db.session.commit()
    session['user_id'] = user.id
    session['user_rol'] = user.rol
    session.permanent = True

    response = jsonify({'user': user.to_dict(),
                        'redirect': _dest_for(user.rol)})
    return _issue_web_session(user, response)


@bp.get('/register')
def register():
    if session.get('user_id'):
        return _redirect_by_role(session.get('user_rol'))
    planteles = Plantel.query.filter_by(activo=True).all()
    carreras = Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).all()
    return render_template('auth/register.html',
                           planteles=planteles, carreras=carreras)


@bp.post('/web-register')
@limiter.limit('20 per hour')
def register_post():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    nombre = (data.get('nombre') or '').strip()
    apellido_p = (data.get('apellido_p') or '').strip()
    apellido_m = (data.get('apellido_m') or '').strip() or None
    rol = data.get('rol') or 'estudiante'

    if not (email and password and nombre and apellido_p):
        return jsonify({'error': 'Faltan campos obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    if rol not in ('estudiante', 'aspirante', 'invitado', 'profesor'):
        return jsonify({'error': 'Rol no permitido',
                        'code': 'INVALID_ROL'}), 422
    if len(password) < 8:
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres',
                        'code': 'WEAK_PASSWORD', 'field': 'password'}), 422
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Ya existe una cuenta con ese correo',
                        'code': 'EMAIL_DUPLICATE', 'field': 'email'}), 409

    user = User(
        email=email, nombre=nombre,
        apellido_p=apellido_p, apellido_m=apellido_m,
        rol=rol, estado='activo',
        plantel_id=data.get('plantel_id'),
        carrera_id=data.get('carrera_id'),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['user_rol'] = user.rol
    session.permanent = True
    response = jsonify({'user': user.to_dict(),
                        'redirect': _dest_for(user.rol)})
    return _issue_web_session(user, response), 201


@bp.get('/logout')
def logout():
    session.clear()
    resp = redirect(url_for('web_public.landing'))
    unset_jwt_cookies(resp)
    return resp


# =============== PASSWORD RESET ===============

# Tokens en memoria por simplicidad. En producción usar tabla DB con expira_at.
_RESET_TOKENS = {}  # token → (user_id, expira_at)


@bp.get('/forgot')
def forgot():
    return render_template('auth/forgot.html')


@bp.post('/forgot')
@limiter.limit('5 per hour')
def forgot_post():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first()
    msg = 'Si la cuenta existe, recibirás un correo con instrucciones.'
    if user and not user.is_deleted and user.estado == 'activo':
        token = secrets.token_urlsafe(32)
        _RESET_TOKENS[token] = (user.id, datetime.utcnow() + timedelta(hours=1))
        # En producción enviarías email; en dev lo logeamos
        if current_app.debug:
            current_app.logger.warning(
                'Reset link (dev) → %s/auth/reset/%s',
                request.host_url.rstrip('/'), token)
            return jsonify({'message': msg, 'dev_token': token,
                            'dev_url': f'/auth/reset/{token}'})
    return jsonify({'message': msg})


@bp.get('/reset/<token>')
def reset(token):
    item = _RESET_TOKENS.get(token)
    if not item or item[1] < datetime.utcnow():
        return render_template('auth/reset.html', token=token, valid=False)
    return render_template('auth/reset.html', token=token, valid=True)


@bp.post('/reset/<token>')
@limiter.limit('5 per hour')
def reset_post(token):
    item = _RESET_TOKENS.get(token)
    if not item or item[1] < datetime.utcnow():
        return jsonify({'error': 'Token inválido o expirado',
                        'code': 'TOKEN_INVALID'}), 400
    data = request.get_json(silent=True) or {}
    nueva = data.get('password_nuevo') or ''
    if len(nueva) < 8:
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres',
                        'code': 'WEAK_PASSWORD'}), 422
    user = User.query.get(item[0])
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    user.set_password(nueva)
    # Revocar todas las sesiones existentes
    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update(
        {'revoked': True})
    db.session.commit()
    _RESET_TOKENS.pop(token, None)
    return jsonify({'message': 'Contraseña restablecida. Inicia sesión.'})


def _dest_for(rol):
    return ({'admin': '/admin', 'director': '/admin', 'coordinador': '/admin',
             'rector': '/admin', 'profesor': '/profesor',
             'invitado': '/oferta', 'aspirante': '/oferta',
             'estudiante': '/dashboard'}).get(rol, '/dashboard')


def _redirect_by_role(rol):
    if rol in ('admin', 'director', 'coordinador', 'rector'):
        return redirect(url_for('web_admin.admin_dashboard'))
    if rol == 'profesor':
        return redirect(url_for('web_profesor.profesor_dashboard'))
    if rol == 'invitado':
        return redirect(url_for('web_public.oferta'))
    return redirect(url_for('web_student.dashboard'))
