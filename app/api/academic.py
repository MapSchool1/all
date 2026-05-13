"""Carreras, materias, periodos académicos."""
from datetime import datetime
from collections import defaultdict
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import (
    Carrera, Materia, PeriodoAcademico, CalendarioAcademico, Plantel, User,
)
from app.utils.decorators import roles_required
from app.utils.audit import write_audit

bp = Blueprint('academic_api', __name__)


# =============== PLANTELES ===============

@bp.get('/planteles')
def list_planteles():
    items = Plantel.query.filter_by(activo=True).order_by(Plantel.nombre).all()
    return jsonify({'data': [p.to_dict() for p in items]})


@bp.put('/planteles/<int:p_id>')
@roles_required('rector', 'admin')
def update_plantel(p_id):
    p = Plantel.query.get(p_id)
    if not p:
        return jsonify({'error': 'Plantel no encontrado',
                        'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('nombre', 'clave', 'ciudad', 'direccion', 'activo'):
        if f in data:
            setattr(p, f, data[f])
    db.session.commit()
    return jsonify({'plantel': p.to_dict()})


@bp.get('/planteles/<int:p_id>/stats')
@roles_required('director', 'admin', 'rector')
def plantel_stats(p_id):
    p = Plantel.query.get(p_id)
    if not p:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    estudiantes = User.query.filter_by(plantel_id=p_id, rol='estudiante',
                                       estado='activo').filter(
        User.deleted_at.is_(None)).count()
    profesores = User.query.filter_by(plantel_id=p_id, rol='profesor',
                                      estado='activo').filter(
        User.deleted_at.is_(None)).count()
    carreras = Carrera.query.filter_by(plantel_id=p_id, activa=True).count()
    return jsonify({
        'plantel': p.to_dict(),
        'estudiantes': estudiantes,
        'profesores': profesores,
        'carreras': carreras,
    })


# =============== CARRERAS ===============

@bp.get('/carreras')
def list_carreras():
    q = Carrera.query.filter(Carrera.deleted_at.is_(None))
    if request.args.get('plantel_id'):
        try:
            q = q.filter_by(plantel_id=int(request.args['plantel_id']))
        except ValueError:
            pass
    if request.args.get('activa'):
        q = q.filter_by(activa=request.args['activa'].lower() == 'true')
    items = q.order_by(Carrera.nombre).all()
    return jsonify({'data': [c.to_dict() for c in items]})


@bp.get('/carreras/<int:c_id>')
def get_carrera(c_id):
    c = Carrera.query.get(c_id)
    if not c or c.deleted_at:
        return jsonify({'error': 'Carrera no encontrada',
                        'code': 'NOT_FOUND'}), 404
    plan = defaultdict(list)
    materias = (Materia.query.filter_by(carrera_id=c_id, activa=True)
                .order_by(Materia.semestre, Materia.clave).all())
    for m in materias:
        plan[str(m.semestre)].append(m.to_dict())
    return jsonify({'carrera': c.to_dict(), 'plan_estudios': dict(plan)})


@bp.get('/carreras/slug/<string:slug>')
def get_carrera_slug(slug):
    c = Carrera.query.filter_by(slug=slug).first()
    if not c or c.deleted_at:
        return jsonify({'error': 'Carrera no encontrada',
                        'code': 'NOT_FOUND'}), 404
    return get_carrera(c.id)


@bp.post('/carreras')
@roles_required('coordinador', 'admin', 'director')
def create_carrera():
    data = request.get_json(silent=True) or {}
    if not data.get('nombre') or not data.get('slug'):
        return jsonify({'error': 'Nombre y slug son obligatorios',
                        'code': 'MISSING_FIELDS'}), 422
    if Carrera.query.filter_by(slug=data['slug']).first():
        return jsonify({'error': 'Slug duplicado', 'code': 'SLUG_DUPLICATE',
                        'field': 'slug'}), 409
    c = Carrera(
        nombre=data['nombre'],
        nombre_corto=data.get('nombre_corto'),
        slug=data['slug'],
        descripcion=data.get('descripcion'),
        duracion_semestres=data.get('duracion_semestres', 8),
        creditos_totales=data.get('creditos_totales', 300),
        campos=data.get('campos'),
        plantel_id=data.get('plantel_id'),
        activa=data.get('activa', True),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'carrera': c.to_dict()}), 201


@bp.put('/carreras/<int:c_id>')
@roles_required('coordinador', 'admin', 'director')
def update_carrera(c_id):
    c = Carrera.query.get(c_id)
    if not c:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('nombre', 'nombre_corto', 'descripcion', 'duracion_semestres',
              'creditos_totales', 'campos', 'plantel_id', 'activa'):
        if f in data:
            setattr(c, f, data[f])
    db.session.commit()
    return jsonify({'carrera': c.to_dict()})


@bp.delete('/carreras/<int:c_id>')
@roles_required('director', 'admin')
def delete_carrera(c_id):
    c = Carrera.query.get(c_id)
    if not c:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    requester_id = int(get_jwt_identity())
    antes = c.to_dict()
    c.deleted_at = datetime.utcnow()
    c.activa = False
    write_audit(requester_id, 'carrera.delete', 'Carrera', c.id,
                payload_antes=antes)
    db.session.commit()
    return jsonify({'message': 'Carrera eliminada'})


# =============== MATERIAS ===============

@bp.get('/materias')
@jwt_required(optional=True)
def list_materias():
    q = Materia.query.filter(Materia.deleted_at.is_(None))
    for f in ('carrera_id', 'semestre'):
        v = request.args.get(f)
        if v:
            try:
                q = q.filter(getattr(Materia, f) == int(v))
            except ValueError:
                pass
    if request.args.get('tipo'):
        q = q.filter_by(tipo=request.args['tipo'])
    if request.args.get('activa'):
        q = q.filter_by(activa=request.args['activa'].lower() == 'true')
    items = q.order_by(Materia.carrera_id, Materia.semestre, Materia.clave).all()
    return jsonify({'data': [m.to_dict() for m in items]})


@bp.get('/materias/<int:m_id>')
@jwt_required()
def get_materia(m_id):
    m = Materia.query.get(m_id)
    if not m or m.deleted_at:
        return jsonify({'error': 'Materia no encontrada',
                        'code': 'NOT_FOUND'}), 404
    from app.models import Inscripcion
    activo = PeriodoAcademico.query.filter_by(activo=True).first()
    inscritos = 0
    if activo:
        inscritos = Inscripcion.query.filter_by(
            materia_id=m_id, periodo_id=activo.id, estado='activa').count()
    return jsonify({
        'materia': m.to_dict(),
        'inscripciones_periodo_actual': inscritos,
    })


@bp.post('/materias')
@roles_required('coordinador', 'admin', 'director')
def create_materia():
    data = request.get_json(silent=True) or {}
    required = ['clave', 'nombre', 'carrera_id', 'semestre', 'tipo']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': 'Faltan campos', 'code': 'MISSING_FIELDS',
                        'fields': missing}), 422
    if Materia.query.filter_by(clave=data['clave']).first():
        return jsonify({'error': 'Clave duplicada', 'code': 'CLAVE_DUPLICATE',
                        'field': 'clave'}), 409
    m = Materia(**{k: data.get(k) for k in (
        'clave', 'nombre', 'nombre_corto', 'carrera_id', 'semestre',
        'tipo', 'creditos', 'horas_teoria', 'horas_practica',
        'prerequisitos', 'activa') if k in data})
    db.session.add(m)
    db.session.commit()
    return jsonify({'materia': m.to_dict()}), 201


@bp.put('/materias/<int:m_id>')
@roles_required('coordinador', 'admin', 'director')
def update_materia(m_id):
    m = Materia.query.get(m_id)
    if not m:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('nombre', 'nombre_corto', 'carrera_id', 'semestre', 'tipo',
              'creditos', 'horas_teoria', 'horas_practica',
              'prerequisitos', 'activa'):
        if f in data:
            setattr(m, f, data[f])
    db.session.commit()
    return jsonify({'materia': m.to_dict()})


@bp.delete('/materias/<int:m_id>')
@roles_required('coordinador', 'admin', 'director')
def delete_materia(m_id):
    m = Materia.query.get(m_id)
    if not m:
        return jsonify({'error': 'No encontrada', 'code': 'NOT_FOUND'}), 404
    m.deleted_at = datetime.utcnow()
    m.activa = False
    db.session.commit()
    return jsonify({'message': 'Materia eliminada'})


# =============== PERIODOS ===============

@bp.get('/periodos')
def list_periodos():
    q = PeriodoAcademico.query
    if request.args.get('plantel_id'):
        try:
            q = q.filter_by(plantel_id=int(request.args['plantel_id']))
        except ValueError:
            pass
    items = q.order_by(PeriodoAcademico.fecha_inicio.desc()).all()
    return jsonify({'data': [p.to_dict() for p in items]})


@bp.get('/periodos/activo')
def periodo_activo():
    plantel_id = request.args.get('plantel_id')
    q = PeriodoAcademico.query.filter_by(activo=True)
    if plantel_id:
        try:
            q = q.filter_by(plantel_id=int(plantel_id))
        except ValueError:
            pass
    p = q.first()
    if not p:
        return jsonify({'periodo': None})
    return jsonify({'periodo': p.to_dict()})


@bp.post('/periodos')
@roles_required('director', 'admin', 'rector')
def create_periodo():
    data = request.get_json(silent=True) or {}
    required = ['clave', 'fecha_inicio', 'fecha_fin']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': 'Faltan campos', 'code': 'MISSING_FIELDS',
                        'fields': missing}), 422
    if PeriodoAcademico.query.filter_by(clave=data['clave']).first():
        return jsonify({'error': 'Clave duplicada',
                        'code': 'CLAVE_DUPLICATE'}), 409
    p = PeriodoAcademico(
        clave=data['clave'],
        nombre=data.get('nombre'),
        plantel_id=data.get('plantel_id'),
        fecha_inicio=datetime.fromisoformat(data['fecha_inicio']).date(),
        fecha_fin=datetime.fromisoformat(data['fecha_fin']).date(),
        apertura_inscripciones=(datetime.fromisoformat(data['apertura_inscripciones'])
                                if data.get('apertura_inscripciones') else None),
        cierre_inscripciones=(datetime.fromisoformat(data['cierre_inscripciones'])
                              if data.get('cierre_inscripciones') else None),
        activo=False,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'periodo': p.to_dict()}), 201


@bp.put('/periodos/<int:p_id>')
@roles_required('director', 'admin', 'rector')
def update_periodo(p_id):
    p = PeriodoAcademico.query.get(p_id)
    if not p:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    data = request.get_json(silent=True) or {}
    for f in ('clave', 'nombre', 'plantel_id'):
        if f in data:
            setattr(p, f, data[f])
    for f in ('fecha_inicio', 'fecha_fin'):
        if f in data and data[f]:
            setattr(p, f, datetime.fromisoformat(data[f]).date())
    for f in ('apertura_inscripciones', 'cierre_inscripciones'):
        if f in data and data[f]:
            setattr(p, f, datetime.fromisoformat(data[f]))
    db.session.commit()
    return jsonify({'periodo': p.to_dict()})


@bp.post('/periodos/<int:p_id>/activar')
@roles_required('director', 'admin', 'rector')
def activar_periodo(p_id):
    p = PeriodoAcademico.query.get(p_id)
    if not p:
        return jsonify({'error': 'No encontrado', 'code': 'NOT_FOUND'}), 404
    PeriodoAcademico.query.filter_by(plantel_id=p.plantel_id,
                                     activo=True).update({'activo': False})
    p.activo = True
    db.session.commit()
    return jsonify({'periodo': p.to_dict()})


@bp.get('/periodos/<int:p_id>/calendario')
@jwt_required(optional=True)
def periodo_calendario(p_id):
    eventos = (CalendarioAcademico.query.filter_by(periodo_id=p_id)
               .order_by(CalendarioAcademico.fecha_inicio).all())
    return jsonify({'eventos': [e.to_dict() for e in eventos]})


@bp.post('/periodos/<int:p_id>/calendario')
@roles_required('coordinador', 'admin', 'director')
def add_evento_calendario(p_id):
    data = request.get_json(silent=True) or {}
    if not data.get('titulo') or not data.get('fecha_inicio'):
        return jsonify({'error': 'Faltan campos',
                        'code': 'MISSING_FIELDS'}), 422
    e = CalendarioAcademico(
        periodo_id=p_id,
        titulo=data['titulo'],
        descripcion=data.get('descripcion'),
        tipo=data.get('tipo', 'evento'),
        fecha_inicio=datetime.fromisoformat(data['fecha_inicio']).date(),
        fecha_fin=(datetime.fromisoformat(data['fecha_fin']).date()
                   if data.get('fecha_fin') else None),
        aplica_a=data.get('aplica_a', 'todos'),
        color=data.get('color'),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'evento': e.to_dict()}), 201
