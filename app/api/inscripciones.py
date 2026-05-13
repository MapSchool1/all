"""Inscripciones, calificaciones, asistencia."""
from datetime import datetime, date as date_cls
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import (
    Inscripcion, Calificacion, RegistroAsistencia, User, Materia,
    PeriodoAcademico,
)
from app.utils.decorators import roles_required
from app.utils.notify import notify

bp = Blueprint('inscripciones_api', __name__)


@bp.get('')
@jwt_required()
def list_inscripciones():
    uid = int(get_jwt_identity())
    q = Inscripcion.query.filter_by(estudiante_id=uid)
    if request.args.get('periodo_id'):
        try:
            q = q.filter_by(periodo_id=int(request.args['periodo_id']))
        except ValueError:
            pass
    items = q.all()
    return jsonify({'data': [i.to_dict() for i in items]})


@bp.post('')
@jwt_required()
def create_inscripcion():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    is_admin = user.rol in ('admin', 'coordinador', 'director')
    data = request.get_json(silent=True) or {}
    estudiante_id = data.get('estudiante_id', uid) if is_admin else uid
    materia_id = data.get('materia_id')
    periodo_id = data.get('periodo_id')
    if not (materia_id and periodo_id):
        return jsonify({'error': 'materia_id y periodo_id son obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    if Inscripcion.query.filter_by(
            estudiante_id=estudiante_id, materia_id=materia_id,
            periodo_id=periodo_id).filter(
        Inscripcion.estado != 'baja').first():
        return jsonify({'error': 'Ya estás inscrito en esa materia',
                        'code': 'DUPLICATE_INSCRIPCION'}), 409
    ins = Inscripcion(
        estudiante_id=estudiante_id,
        materia_id=materia_id,
        periodo_id=periodo_id,
        grupo=data.get('grupo'),
        profesor_id=data.get('profesor_id'),
        estado='activa',
    )
    db.session.add(ins)
    db.session.commit()
    return jsonify({'inscripcion': ins.to_dict()}), 201


@bp.delete('/<int:i_id>')
@jwt_required()
def baja_inscripcion(i_id):
    ins = Inscripcion.query.get(i_id)
    if not ins:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if ins.estudiante_id != uid and user.rol not in (
            'admin', 'coordinador', 'director'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    ins.estado = 'baja'
    db.session.commit()
    return jsonify({'message': 'Baja registrada'})


# =============== CALIFICACIONES ===============

@bp.get('/<int:i_id>/calificaciones')
@jwt_required()
def list_calificaciones(i_id):
    ins = Inscripcion.query.get(i_id)
    if not ins:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if (ins.estudiante_id != uid and ins.profesor_id != uid
            and user.rol not in ('admin', 'coordinador', 'director')):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    publicar_filter = ins.estudiante_id == uid
    califs = ins.calificaciones
    if publicar_filter:
        califs = [c for c in califs if c.publicado]
    return jsonify({'calificaciones': [c.to_dict() for c in califs]})


@bp.put('/<int:i_id>/calificaciones')
@roles_required('profesor', 'admin', 'coordinador')
def upsert_calificacion(i_id):
    ins = Inscripcion.query.get(i_id)
    if not ins:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user.rol == 'profesor' and ins.profesor_id != uid:
        return jsonify({'error': 'No eres el profesor de esta inscripción',
                        'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    tipo = data.get('tipo')
    valor = data.get('valor')
    if tipo not in ('parcial_1', 'parcial_2', 'parcial_3',
                    'ordinario', 'extraordinario', 'final'):
        return jsonify({'error': 'Tipo inválido', 'code': 'INVALID_TIPO'}), 422
    try:
        valor = float(valor) if valor is not None else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Valor inválido',
                        'code': 'INVALID_VALOR'}), 422
    if valor is not None and not (0 <= valor <= 10):
        return jsonify({'error': 'El valor debe estar entre 0 y 10',
                        'code': 'INVALID_VALOR'}), 422
    c = Calificacion.query.filter_by(inscripcion_id=i_id, tipo=tipo).first()
    if not c:
        c = Calificacion(inscripcion_id=i_id, tipo=tipo)
        db.session.add(c)
    c.valor = valor
    c.observaciones = data.get('observaciones')
    c.capturado_por = uid
    c.capturado_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'calificacion': c.to_dict()})


@bp.post('/<int:i_id>/calificaciones/publicar')
@roles_required('coordinador', 'admin', 'director')
def publicar_calificaciones(i_id):
    ins = Inscripcion.query.get(i_id)
    if not ins:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    for c in ins.calificaciones:
        if not c.publicado:
            c.publicado = True
            c.publicado_at = datetime.utcnow()
    notify(ins.estudiante_id, 'calificacion',
           'Tus calificaciones se publicaron',
           f'Revisa tus calificaciones de {ins.materia.nombre if ins.materia else ""}.',
           accion_url='/dashboard?tab=calificaciones', commit=False)
    db.session.commit()
    return jsonify({'calificaciones': [c.to_dict() for c in ins.calificaciones]})


# =============== ASISTENCIA ===============

@bp.get('/<int:i_id>/asistencia')
@jwt_required()
def get_asistencia(i_id):
    ins = Inscripcion.query.get(i_id)
    if not ins:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if (ins.estudiante_id != uid and ins.profesor_id != uid
            and user.rol not in ('admin', 'coordinador', 'director')):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    regs = RegistroAsistencia.query.filter_by(
        inscripcion_id=i_id).order_by(RegistroAsistencia.fecha).all()
    total = len(regs)
    pres = sum(1 for r in regs if r.estado == 'presente')
    just = sum(1 for r in regs if r.estado == 'justificado')
    faltas = sum(1 for r in regs if r.estado == 'ausente')
    pct = round((pres + just) / total * 100, 1) if total else None
    return jsonify({
        'registros': [r.to_dict() for r in regs],
        'porcentaje': pct,
        'faltas': faltas,
        'justificadas': just,
        'total': total,
    })


@bp.post('/asistencia/masiva')
@roles_required('profesor', 'admin', 'coordinador')
def asistencia_masiva():
    data = request.get_json(silent=True) or {}
    bloque_id = data.get('bloque_id')
    fecha_str = data.get('fecha')
    registros = data.get('registros', [])
    if not (bloque_id and fecha_str and registros):
        return jsonify({'error': 'bloque_id, fecha y registros requeridos',
                        'code': 'MISSING_FIELDS'}), 422
    try:
        fecha = datetime.fromisoformat(fecha_str).date() \
            if 'T' in fecha_str else date_cls.fromisoformat(fecha_str)
    except ValueError:
        return jsonify({'error': 'Fecha inválida',
                        'code': 'INVALID_DATE'}), 422
    uid = int(get_jwt_identity())
    procesados = 0
    for r in registros:
        existente = RegistroAsistencia.query.filter_by(
            inscripcion_id=r['inscripcion_id'],
            bloque_id=bloque_id,
            fecha=fecha).first()
        if existente:
            existente.estado = r['estado']
            existente.justificacion = r.get('justificacion')
        else:
            db.session.add(RegistroAsistencia(
                inscripcion_id=r['inscripcion_id'],
                bloque_id=bloque_id, fecha=fecha,
                estado=r['estado'],
                justificacion=r.get('justificacion'),
                registrado_por=uid,
            ))
        procesados += 1
    db.session.commit()
    return jsonify({'procesados': procesados})
