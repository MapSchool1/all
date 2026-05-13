"""Página de demostración del sistema de componentes (solo en DEBUG)."""
from flask import Blueprint, render_template

from app.models import (
    User, Salon, Materia, Bloque, Horario, PeriodoAcademico,
)

bp = Blueprint('web_components', __name__)


@bp.get('')
@bp.get('/')
def components_demo():
    users_demo = User.query.filter(User.deleted_at.is_(None)).limit(8).all()
    salones_demo = Salon.query.filter_by(activo=True).filter(
        Salon.deleted_at.is_(None)).limit(6).all()
    materias_demo = Materia.query.filter_by(activa=True).filter(
        Materia.deleted_at.is_(None)).limit(6).all()
    horario_demo = (Horario.query.filter(Horario.deleted_at.is_(None))
                    .order_by(Horario.id).first())
    bloques_demo = []
    if horario_demo:
        bloques_demo = sorted(horario_demo.bloques,
                              key=lambda b: (('lun', 'mar', 'mie',
                                              'jue', 'vie', 'sab')
                                             .index(b.dia), b.hora_inicio))
    return render_template('components/demo.html',
                           users=users_demo,
                           salones=salones_demo,
                           materias=materias_demo,
                           horario=horario_demo,
                           bloques=bloques_demo)
