from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from app.extensions import db
from app.models import User, Horario, Tramite, Inscripcion, RegistroAsistencia
from app.utils.decorators import roles_required
from app.utils.pagination import paginate
from app.utils.audit import write_audit

bp = Blueprint('users_api', __name__)


def _filter_active(query):
    return query.filter(User.deleted_at.is_(None))


@bp.get('')
@roles_required('admin', 'director', 'coordinador', 'rector')
def list_users():
    q = _filter_active(User.query)
    search = request.args.get('search')
    if search:
        like = f'%{search}%'
        q = q.filter(or_(User.nombre.ilike(like),
                         User.apellido_p.ilike(like),
                         User.email.ilike(like),
                         User.expediente.ilike(like)))
    for field in ('rol', 'estado'):
        val = request.args.get(field)
        if val:
            q = q.filter(getattr(User, field) == val)
    for field in ('plantel_id', 'carrera_id'):
        val = request.args.get(field)
        if val:
            try:
                q = q.filter(getattr(User, field) == int(val))
            except ValueError:
                pass
    q = q.order_by(User.created_at.desc())
    items, meta = paginate(q)
    return jsonify({'data': [u.to_dict() for u in items], **meta})


@bp.get('/<int:user_id>')
@jwt_required()
def get_user(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    if not requester:
        return jsonify({'error': 'No autenticado', 'code': 'UNAUTHORIZED'}), 401
    if requester.id != user_id and requester.rol not in (
            'admin', 'director', 'coordinador', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    horarios_count = Horario.query.filter_by(
        user_id=user_id).filter(Horario.deleted_at.is_(None)).count()
    tramites_count = Tramite.query.filter_by(solicitante_id=user_id).count()
    inscripciones = Inscripcion.query.filter_by(estudiante_id=user_id).all()
    asistencias = []
    for ins in inscripciones:
        regs = RegistroAsistencia.query.filter_by(inscripcion_id=ins.id).all()
        if regs:
            pres = sum(1 for r in regs if r.estado in ('presente', 'justificado'))
            asistencias.append(pres / len(regs) * 100)
    asist_prom = round(sum(asistencias) / len(asistencias), 1) if asistencias else None
    return jsonify({
        'user': user.to_dict(),
        'estadisticas': {
            'horarios': horarios_count,
            'tramites': tramites_count,
            'asistencia_prom': asist_prom,
        },
    })


@bp.post('')
@roles_required('admin')
def create_user():
    data = request.get_json(silent=True) or {}
    required = ['nombre', 'apellido_p', 'email', 'rol']
    missing = [f for f in required if not (data.get(f) or '').strip()]
    if missing:
        return jsonify({'error': 'Faltan campos obligatorios',
                        'code': 'MISSING_FIELDS', 'fields': missing}), 422
    email = data['email'].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Ya existe una cuenta con ese correo',
                        'code': 'EMAIL_DUPLICATE', 'field': 'email'}), 409
    password = data.get('password_temporal') or 'Cambiar123!'
    user = User(
        nombre=data['nombre'].strip(),
        apellido_p=data['apellido_p'].strip(),
        apellido_m=(data.get('apellido_m') or '').strip() or None,
        email=email,
        rol=data['rol'],
        plantel_id=data.get('plantel_id'),
        carrera_id=data.get('carrera_id'),
        expediente=data.get('expediente'),
        semestre_actual=data.get('semestre_actual'),
        avatar_color=data.get('avatar_color') or '#172846',
        estado='activo',
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    write_audit(int(get_jwt_identity()), 'user.create',
                'User', user.id, payload_despues=user.to_dict())
    db.session.commit()
    return jsonify({'user': user.to_dict()}), 201


@bp.put('/<int:user_id>')
@jwt_required()
def update_user(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    is_admin = requester.rol in ('admin', 'director', 'rector')
    if requester.id != user_id and not is_admin:
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403

    data = request.get_json(silent=True) or {}
    antes = user.to_dict()

    self_fields = ('nombre', 'apellido_p', 'apellido_m', 'telefono',
                   'avatar_color')
    admin_fields = ('rol', 'estado', 'plantel_id', 'carrera_id',
                    'expediente', 'semestre_actual')

    for f in self_fields:
        if f in data:
            setattr(user, f, data[f])
    if is_admin:
        for f in admin_fields:
            if f in data:
                setattr(user, f, data[f])

    db.session.flush()
    if is_admin:
        write_audit(requester.id, 'user.update', 'User', user.id,
                    payload_antes=antes, payload_despues=user.to_dict())
    db.session.commit()
    return jsonify({'user': user.to_dict()})


@bp.delete('/<int:user_id>')
@roles_required('admin')
def delete_user(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    if user.id == requester.id:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta',
                        'code': 'SELF_DELETE'}), 422
    antes = user.to_dict()
    user.deleted_at = datetime.utcnow()
    user.estado = 'eliminado'
    write_audit(requester.id, 'user.delete', 'User', user.id,
                payload_antes=antes, payload_despues=user.to_dict())
    db.session.commit()
    return jsonify({'message': 'Usuario eliminado'})


@bp.post('/<int:user_id>/suspender')
@roles_required('admin', 'director', 'rector')
def suspender_user(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    antes = user.to_dict()
    user.estado = 'suspendido'
    write_audit(requester.id, 'user.suspend', 'User', user.id,
                payload_antes=antes,
                payload_despues={'motivo': data.get('motivo')})
    db.session.commit()
    return jsonify({'user': user.to_dict()})


@bp.post('/<int:user_id>/restablecer')
@roles_required('admin')
def restablecer_user(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'Usuario no encontrado',
                        'code': 'NOT_FOUND'}), 404
    antes = user.to_dict()
    user.estado = 'activo'
    user.intentos_fallidos = 0
    write_audit(requester.id, 'user.restore', 'User', user.id,
                payload_antes=antes, payload_despues=user.to_dict())
    db.session.commit()
    return jsonify({'user': user.to_dict()})


@bp.get('/<int:user_id>/horarios')
@jwt_required()
def user_horarios(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    if requester.id != user_id and requester.rol not in (
            'admin', 'director', 'coordinador', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    horarios = (Horario.query
                .filter(Horario.user_id == user_id,
                        Horario.deleted_at.is_(None))
                .order_by(Horario.updated_at.desc()).all())
    return jsonify({'horarios': [h.to_dict() for h in horarios]})


@bp.get('/<int:user_id>/tramites')
@jwt_required()
def user_tramites(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    if requester.id != user_id and requester.rol not in (
            'admin', 'director', 'coordinador', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    tramites = (Tramite.query.filter_by(solicitante_id=user_id)
                .order_by(Tramite.created_at.desc()).all())
    return jsonify({'tramites': [t.to_dict() for t in tramites]})


@bp.get('/<int:user_id>/calificaciones')
@jwt_required()
def user_calificaciones(user_id):
    requester = User.query.get(int(get_jwt_identity()))
    if (requester.id != user_id and requester.rol not in (
            'admin', 'director', 'coordinador', 'rector', 'profesor')):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    inscripciones = Inscripcion.query.filter_by(
        estudiante_id=user_id).all()
    out = []
    for ins in inscripciones:
        regs = RegistroAsistencia.query.filter_by(inscripcion_id=ins.id).all()
        pct = (sum(1 for r in regs if r.estado in ('presente', 'justificado'))
               / len(regs) * 100) if regs else None
        out.append({
            **ins.to_dict(),
            'calificaciones': [c.to_dict() for c in ins.calificaciones],
            'asistencia_pct': round(pct, 1) if pct is not None else None,
        })
    return jsonify({'inscripciones': out})
