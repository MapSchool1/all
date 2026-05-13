"""Horarios y bloques (con detección de conflictos)."""
from datetime import datetime, time
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import (
    Horario, Bloque, Materia, Salon, User, PeriodoAcademico,
    PlantillaHorario,
)
from app.utils.decorators import roles_required
from app.utils.pagination import paginate
from app.utils.audit import write_audit
from app.utils.notify import notify
from app.utils.conflicts import (
    detectar_conflictos_horario, salon_disponible,
)

bp = Blueprint('horarios_api', __name__)


def _can_view(horario: Horario, user: User) -> bool:
    if horario.user_id == user.id:
        return True
    return user.rol in ('admin', 'director', 'coordinador', 'rector')


def _recalcular_totales(horario: Horario):
    creditos = 0
    horas = 0
    seen_materia = set()
    for b in horario.bloques:
        if b.materia and b.materia.id not in seen_materia:
            creditos += (b.materia.creditos or 0)
            seen_materia.add(b.materia.id)
        if b.hora_inicio and b.hora_fin:
            delta = (datetime.combine(datetime.today(), b.hora_fin)
                     - datetime.combine(datetime.today(), b.hora_inicio))
            horas += int(delta.total_seconds() // 3600)
    horario.total_creditos = creditos
    horario.total_horas = horas


@bp.get('')
@jwt_required()
def list_horarios():
    uid = int(get_jwt_identity())
    q = Horario.query.filter(Horario.user_id == uid,
                             Horario.deleted_at.is_(None))
    if request.args.get('periodo_id'):
        try:
            q = q.filter_by(periodo_id=int(request.args['periodo_id']))
        except ValueError:
            pass
    if request.args.get('estado'):
        q = q.filter_by(estado=request.args['estado'])
    items = q.order_by(Horario.updated_at.desc()).all()
    return jsonify({'data': [h.to_dict() for h in items]})


@bp.post('')
@jwt_required()
def create_horario():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    periodo_id = data.get('periodo_id')
    if not periodo_id:
        p = PeriodoAcademico.query.filter_by(activo=True).first()
        if p:
            periodo_id = p.id
    if not periodo_id:
        return jsonify({'error': 'periodo_id requerido',
                        'code': 'MISSING_FIELDS', 'field': 'periodo_id'}), 422
    existing = (Horario.query.filter(Horario.user_id == uid,
                                     Horario.periodo_id == periodo_id,
                                     Horario.estado != 'archivado',
                                     Horario.deleted_at.is_(None)).first())
    if existing:
        return jsonify({'error': 'Ya tienes un horario activo para este periodo',
                        'code': 'HORARIO_DUPLICATE',
                        'horario': existing.to_dict()}), 409
    h = Horario(user_id=uid, periodo_id=periodo_id,
                nombre=data.get('nombre') or 'Mi horario',
                estado='borrador')
    db.session.add(h)
    db.session.commit()
    return jsonify({'horario': h.to_dict()}), 201


@bp.get('/<int:h_id>')
@jwt_required()
def get_horario(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    user = User.query.get(int(get_jwt_identity()))
    if not _can_view(h, user):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    bloques = sorted(h.bloques, key=lambda b: (
        ('lun', 'mar', 'mie', 'jue', 'vie', 'sab').index(b.dia),
        b.hora_inicio))
    materias_unicas = {b.materia_id for b in h.bloques if b.materia_id}
    conflictos = sum(1 for b in h.bloques if b.conflicto)
    return jsonify({
        'horario': h.to_dict(include_user=True),
        'bloques': [b.to_dict() for b in bloques],
        'stats': {
            'total_creditos': h.total_creditos,
            'total_horas': h.total_horas,
            'materias_count': len(materias_unicas),
            'conflictos_count': conflictos,
        },
    })


@bp.put('/<int:h_id>')
@jwt_required()
def update_horario(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    if h.user_id != uid:
        user = User.query.get(uid)
        if user.rol not in ('admin', 'coordinador', 'director', 'rector'):
            return jsonify({'error': 'Permiso denegado',
                            'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    if 'nombre' in data:
        h.nombre = data['nombre']
    if 'estado' in data:
        nuevo = data['estado']
        if nuevo == 'publicado' and h.tiene_conflictos:
            return jsonify({'error': 'No puedes publicar un horario con '
                            'conflictos sin resolver',
                            'code': 'HORARIO_CONFLICTS'}), 422
        h.estado = nuevo
        if nuevo == 'publicado':
            h.publicado_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'horario': h.to_dict()})


@bp.delete('/<int:h_id>')
@jwt_required()
def delete_horario(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    if h.user_id != uid:
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    if h.estado != 'borrador':
        return jsonify({'error': 'Solo puedes eliminar horarios en borrador',
                        'code': 'HORARIO_NOT_DRAFT'}), 422
    h.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Horario eliminado'})


@bp.post('/<int:h_id>/publicar')
@jwt_required()
def publicar_horario(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if h.user_id != uid and user.rol not in (
            'admin', 'coordinador', 'director', 'rector'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    detectar_conflictos_horario(h.id)
    if h.tiene_conflictos:
        return jsonify({'error': 'El horario tiene conflictos sin resolver',
                        'code': 'HORARIO_CONFLICTS'}), 422
    h.estado = 'publicado'
    h.publicado_at = datetime.utcnow()
    write_audit(uid, 'horario.publish', 'Horario', h.id,
                payload_despues={'estado': 'publicado',
                                 'publicado_at': h.publicado_at.isoformat()})
    notify(h.user_id, 'horario',
           'Tu horario fue publicado',
           f'Tu horario "{h.nombre}" para el periodo está publicado.',
           accion_url=f'/horario',
           commit=False)
    db.session.commit()
    return jsonify({'horario': h.to_dict()})


@bp.post('/<int:h_id>/clonar')
@jwt_required()
def clonar_horario(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    if h.user_id != uid:
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    nuevo = Horario(user_id=uid, periodo_id=h.periodo_id,
                    nombre=f'{h.nombre} (copia)', estado='borrador')
    db.session.add(nuevo)
    db.session.flush()
    for b in h.bloques:
        nb = Bloque(horario_id=nuevo.id, materia_id=b.materia_id,
                    salon_id=b.salon_id, profesor_id=b.profesor_id,
                    dia=b.dia, hora_inicio=b.hora_inicio,
                    hora_fin=b.hora_fin, tipo_sesion=b.tipo_sesion)
        db.session.add(nb)
    db.session.flush()
    detectar_conflictos_horario(nuevo.id)
    _recalcular_totales(nuevo)
    db.session.commit()
    return jsonify({'horario': nuevo.to_dict()}), 201


# =============== BLOQUES ===============

@bp.post('/<int:h_id>/bloques')
@jwt_required()
def add_bloque(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if h.user_id != uid and user.rol not in ('admin', 'coordinador'):
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    required = ['materia_id', 'dia', 'hora_inicio', 'hora_fin']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': 'Faltan campos',
                        'code': 'MISSING_FIELDS', 'fields': missing}), 422
    try:
        h_i = time.fromisoformat(data['hora_inicio'])
        h_f = time.fromisoformat(data['hora_fin'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Hora inválida',
                        'code': 'INVALID_TIME'}), 422
    if h_i >= h_f:
        return jsonify({'error': 'La hora de inicio debe ser anterior a la final',
                        'code': 'INVALID_RANGE'}), 422
    if data['dia'] not in ('lun', 'mar', 'mie', 'jue', 'vie', 'sab'):
        return jsonify({'error': 'Día inválido', 'code': 'INVALID_DAY'}), 422
    if not Materia.query.get(data['materia_id']):
        return jsonify({'error': 'Materia no encontrada',
                        'code': 'NOT_FOUND'}), 404

    advertencia = None
    if data.get('salon_id'):
        libre, conflicto_b = salon_disponible(
            data['salon_id'], data['dia'], h_i, h_f, h.periodo_id)
        if not libre:
            advertencia = (f'El salón ya está ocupado en ese horario '
                           f'(materia: {conflicto_b.materia.nombre if conflicto_b.materia else "—"}).')

    b = Bloque(
        horario_id=h.id, materia_id=data['materia_id'],
        salon_id=data.get('salon_id'),
        profesor_id=data.get('profesor_id'),
        dia=data['dia'], hora_inicio=h_i, hora_fin=h_f,
        tipo_sesion=data.get('tipo_sesion', 'teoria'),
        notas=data.get('notas'),
    )
    db.session.add(b)
    db.session.flush()
    en_conflicto = detectar_conflictos_horario(h.id)
    _recalcular_totales(h)
    db.session.commit()
    response = {'bloque': b.to_dict()}
    if en_conflicto:
        conflict_blocks = Bloque.query.filter(
            Bloque.id.in_(en_conflicto)).all()
        response['conflictos'] = [cb.to_dict() for cb in conflict_blocks
                                  if cb.id != b.id]
    if advertencia:
        response['advertencia'] = advertencia
    return jsonify(response)


@bp.put('/<int:h_id>/bloques/<int:b_id>')
@jwt_required()
def update_bloque(h_id, b_id):
    b = Bloque.query.get(b_id)
    if not b or b.horario_id != h_id:
        return jsonify({'error': 'Bloque no encontrado',
                        'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    h = b.horario
    if h.user_id != uid:
        user = User.query.get(uid)
        if user.rol not in ('admin', 'coordinador'):
            return jsonify({'error': 'Permiso denegado',
                            'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    if 'hora_inicio' in data:
        b.hora_inicio = time.fromisoformat(data['hora_inicio'])
    if 'hora_fin' in data:
        b.hora_fin = time.fromisoformat(data['hora_fin'])
    for f in ('materia_id', 'salon_id', 'profesor_id', 'dia',
              'tipo_sesion', 'notas'):
        if f in data:
            setattr(b, f, data[f])
    db.session.flush()
    detectar_conflictos_horario(h.id)
    _recalcular_totales(h)
    db.session.commit()
    return jsonify({'bloque': b.to_dict()})


@bp.delete('/<int:h_id>/bloques/<int:b_id>')
@jwt_required()
def delete_bloque(h_id, b_id):
    b = Bloque.query.get(b_id)
    if not b or b.horario_id != h_id:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    h = b.horario
    if h.user_id != uid:
        user = User.query.get(uid)
        if user.rol not in ('admin', 'coordinador'):
            return jsonify({'error': 'Permiso denegado',
                            'code': 'FORBIDDEN'}), 403
    db.session.delete(b)
    db.session.flush()
    detectar_conflictos_horario(h.id)
    _recalcular_totales(h)
    db.session.commit()
    return jsonify({'message': 'Bloque eliminado'})


# =============== HORARIOS ADMIN ===============

@bp.get('/admin')
@roles_required('admin', 'coordinador', 'director', 'rector')
def admin_list():
    q = Horario.query.filter(Horario.deleted_at.is_(None))
    if request.args.get('user_id'):
        try:
            q = q.filter_by(user_id=int(request.args['user_id']))
        except ValueError:
            pass
    if request.args.get('periodo_id'):
        try:
            q = q.filter_by(periodo_id=int(request.args['periodo_id']))
        except ValueError:
            pass
    if request.args.get('estado'):
        q = q.filter_by(estado=request.args['estado'])
    if request.args.get('carrera_id'):
        try:
            cid = int(request.args['carrera_id'])
            q = q.join(User, User.id == Horario.user_id).filter(
                User.carrera_id == cid)
        except ValueError:
            pass
    q = q.order_by(Horario.updated_at.desc())
    items, meta = paginate(q)
    return jsonify({'data': [h.to_dict(include_user=True) for h in items],
                    **meta})


@bp.get('/admin/vista-carrera')
@roles_required('admin', 'coordinador', 'director', 'rector')
def vista_carrera():
    try:
        carrera_id = int(request.args.get('carrera_id', 0))
        semestre = int(request.args.get('semestre', 0))
    except ValueError:
        return jsonify({'error': 'Parámetros inválidos',
                        'code': 'INVALID_PARAMS'}), 422
    periodo_id = (int(request.args['periodo_id'])
                  if request.args.get('periodo_id') else
                  (PeriodoAcademico.query.filter_by(activo=True).first().id
                   if PeriodoAcademico.query.filter_by(activo=True).first()
                   else None))
    if not (carrera_id and semestre and periodo_id):
        return jsonify({'error': 'Faltan parámetros',
                        'code': 'MISSING_PARAMS'}), 422
    horarios = (Horario.query.join(User, User.id == Horario.user_id)
                .filter(User.carrera_id == carrera_id,
                        User.semestre_actual == semestre,
                        Horario.periodo_id == periodo_id,
                        Horario.deleted_at.is_(None)).all())
    bloques = []
    conflictos = 0
    for h in horarios:
        for b in h.bloques:
            d = b.to_dict()
            d['user'] = {'id': h.usuario.id,
                         'nombre_completo': h.usuario.nombre_completo}
            bloques.append(d)
            if b.conflicto:
                conflictos += 1
    return jsonify({
        'bloques_consolidados': bloques,
        'conflictos_globales': conflictos,
        'horarios_count': len(horarios),
    })


@bp.get('/admin/vista-salon')
@roles_required('admin', 'coordinador', 'director', 'rector')
def vista_salon():
    try:
        salon_id = int(request.args['salon_id'])
    except (KeyError, ValueError):
        return jsonify({'error': 'salon_id requerido',
                        'code': 'MISSING_PARAMS'}), 422
    s = Salon.query.get(salon_id)
    if not s:
        return jsonify({'error': 'Salón no encontrado',
                        'code': 'NOT_FOUND'}), 404
    from app.api.campus import _salon_full
    return jsonify(_salon_full(s))


@bp.get('/admin/vista-profesor')
@roles_required('admin', 'coordinador', 'director', 'rector')
def vista_profesor():
    try:
        profesor_id = int(request.args['profesor_id'])
    except (KeyError, ValueError):
        return jsonify({'error': 'profesor_id requerido',
                        'code': 'MISSING_PARAMS'}), 422
    periodo_id = request.args.get('periodo_id')
    if periodo_id:
        try:
            periodo_id = int(periodo_id)
        except ValueError:
            periodo_id = None
    if not periodo_id:
        p = PeriodoAcademico.query.filter_by(activo=True).first()
        periodo_id = p.id if p else None
    q = Bloque.query.join(Horario, Horario.id == Bloque.horario_id).filter(
        Bloque.profesor_id == profesor_id,
        Horario.deleted_at.is_(None))
    if periodo_id:
        q = q.filter(Horario.periodo_id == periodo_id)
    bloques = q.all()
    return jsonify({'bloques': [b.to_dict() for b in bloques]})


# =============== PLANTILLAS ===============

@bp.get('/plantillas')
@roles_required('admin', 'coordinador', 'director', 'profesor')
def list_plantillas():
    q = PlantillaHorario.query.filter_by(activa=True)
    for f in ('carrera_id', 'semestre', 'periodo_id'):
        v = request.args.get(f)
        if v:
            try:
                q = q.filter(getattr(PlantillaHorario, f) == int(v))
            except ValueError:
                pass
    items = q.all()
    return jsonify({'data': [p.to_dict() for p in items]})


@bp.post('/plantillas')
@roles_required('admin', 'coordinador', 'director')
def create_plantilla():
    data = request.get_json(silent=True) or {}
    p = PlantillaHorario(
        carrera_id=data.get('carrera_id'),
        semestre=data.get('semestre'),
        periodo_id=data.get('periodo_id'),
        nombre=data.get('nombre'),
        bloques=data.get('bloques', []),
        created_by=int(get_jwt_identity()),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'plantilla': p.to_dict()}), 201


@bp.post('/<int:h_id>/aplicar-plantilla')
@jwt_required()
def aplicar_plantilla(h_id):
    h = Horario.query.get(h_id)
    if not h or h.deleted_at:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    uid = int(get_jwt_identity())
    if h.user_id != uid:
        return jsonify({'error': 'Permiso denegado',
                        'code': 'FORBIDDEN'}), 403
    data = request.get_json(silent=True) or {}
    p = PlantillaHorario.query.get(data.get('plantilla_id'))
    if not p:
        return jsonify({'error': 'Plantilla no encontrada',
                        'code': 'NOT_FOUND'}), 404
    creados = 0
    for spec in (p.bloques or []):
        try:
            b = Bloque(
                horario_id=h.id,
                materia_id=spec['materia_id'],
                salon_id=spec.get('salon_id'),
                dia=spec['dia'],
                hora_inicio=time.fromisoformat(spec['hora_inicio']),
                hora_fin=time.fromisoformat(spec['hora_fin']),
                tipo_sesion=spec.get('tipo_sesion', 'teoria'),
            )
            db.session.add(b)
            creados += 1
        except (KeyError, ValueError):
            continue
    db.session.flush()
    en_conflicto = detectar_conflictos_horario(h.id)
    _recalcular_totales(h)
    db.session.commit()
    return jsonify({
        'bloques_creados': creados,
        'conflictos': len(en_conflicto),
        'bloques': [b.to_dict() for b in h.bloques],
    })
