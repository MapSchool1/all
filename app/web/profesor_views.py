"""Vistas web del portal del profesor."""
from flask import Blueprint, render_template, redirect, url_for, session

from app.models import User, Bloque, Inscripcion, PeriodoAcademico

bp = Blueprint('web_profesor', __name__)


def _require_profesor():
    uid = session.get('user_id')
    if not uid:
        return None
    user = User.query.get(uid)
    if not user or user.is_deleted:
        return None
    if user.rol not in ('profesor', 'admin'):
        return None
    return user


@bp.get('')
@bp.get('/')
def profesor_dashboard():
    user = _require_profesor()
    if not user:
        return redirect(url_for('web_auth.login'))
    bloques = Bloque.query.filter_by(profesor_id=user.id).all()
    grupos = Inscripcion.query.filter_by(profesor_id=user.id).all()
    return render_template('profesor/dashboard.html',
                           user=user, bloques=bloques, grupos=grupos)


@bp.get('/horario')
def profesor_horario():
    user = _require_profesor()
    if not user:
        return redirect(url_for('web_auth.login'))
    periodo = PeriodoAcademico.query.filter_by(activo=True).first()
    bloques = (Bloque.query.filter_by(profesor_id=user.id).all()
               if periodo else [])
    return render_template('profesor/horario.html',
                           user=user, bloques=bloques, periodo=periodo)


@bp.get('/grupos/<int:inscripcion_id>')
def grupo(inscripcion_id):
    user = _require_profesor()
    if not user:
        return redirect(url_for('web_auth.login'))
    ins = Inscripcion.query.get_or_404(inscripcion_id)
    grupo_estudiantes = Inscripcion.query.filter_by(
        materia_id=ins.materia_id,
        periodo_id=ins.periodo_id,
        grupo=ins.grupo).all()
    return render_template('profesor/grupo.html',
                           user=user, inscripcion=ins,
                           grupo_estudiantes=grupo_estudiantes)
