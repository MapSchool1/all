"""Vistas web públicas (sin autenticación)."""
from flask import Blueprint, render_template, abort

from app.models import Salon, Carrera, Edificio, PuntoInteres, User, Horario

bp = Blueprint('web_public', __name__)


@bp.get('/')
def landing():
    estudiantes = User.query.filter_by(rol='estudiante', estado='activo').filter(
        User.deleted_at.is_(None)).count()
    horarios = Horario.query.filter_by(estado='publicado').filter(
        Horario.deleted_at.is_(None)).count()
    salones = Salon.query.filter_by(activo=True).filter(
        Salon.deleted_at.is_(None)).count()
    carreras = (Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).limit(3).all())
    return render_template('public/landing.html',
                           stats={'estudiantes': estudiantes,
                                  'horarios': horarios,
                                  'salones': salones},
                           carreras=carreras)


@bp.get('/oferta')
def oferta():
    carreras = Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).order_by(Carrera.nombre).all()
    return render_template('public/oferta.html', carreras=carreras)


@bp.get('/oferta/<string:slug>')
def carrera_detalle(slug):
    c = Carrera.query.filter_by(slug=slug).first()
    if not c or c.deleted_at:
        abort(404)
    plan = {}
    from app.models import Materia
    materias = (Materia.query.filter_by(carrera_id=c.id, activa=True)
                .order_by(Materia.semestre, Materia.clave).all())
    for m in materias:
        plan.setdefault(m.semestre, []).append(m)
    return render_template('public/carrera_detalle.html',
                           carrera=c, plan=plan)


@bp.get('/salones')
def salones():
    edificios = Edificio.query.filter_by(activo=True).order_by(
        Edificio.clave).all()
    salones_qs = Salon.query.filter_by(activo=True).filter(
        Salon.deleted_at.is_(None)).order_by(Salon.codigo).all()
    return render_template('public/salones.html',
                           edificios=edificios, salones=salones_qs)


@bp.get('/salones/<string:codigo>')
def salon_detalle(codigo):
    s = Salon.query.filter_by(codigo=codigo).first()
    if not s or s.deleted_at:
        abort(404)
    return render_template('public/salon_detalle.html', salon=s)


@bp.get('/mapa')
def mapa():
    edificios = Edificio.query.filter_by(activo=True).all()
    puntos = PuntoInteres.query.filter_by(activo=True).all()
    return render_template('public/mapa.html',
                           edificios=edificios, puntos=puntos)
