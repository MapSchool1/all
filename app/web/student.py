"""Vistas web del estudiante."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, session

from app.models import (
    User, Horario, Inscripcion, Tramite, Anuncio, PeriodoAcademico,
    TipoTramite,
)

bp = Blueprint('web_student', __name__)


def _require_login():
    uid = session.get('user_id')
    if not uid:
        return None
    user = User.query.get(uid)
    if not user or user.is_deleted:
        session.clear()
        return None
    return user


@bp.get('/dashboard')
def dashboard():
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    periodo = PeriodoAcademico.query.filter_by(activo=True).first()
    horario = (Horario.query.filter(Horario.user_id == user.id,
                                    Horario.deleted_at.is_(None))
               .order_by(Horario.updated_at.desc()).first())
    bloques = sorted(horario.bloques if horario else [],
                     key=lambda b: (('lun', 'mar', 'mie', 'jue', 'vie', 'sab')
                                    .index(b.dia), b.hora_inicio))
    inscripciones = Inscripcion.query.filter_by(
        estudiante_id=user.id).all() if periodo else []
    tramites = (Tramite.query.filter_by(solicitante_id=user.id)
                .order_by(Tramite.created_at.desc()).all())
    anuncios = (Anuncio.query.filter_by(publicado=True, fijado=True)
                .order_by(Anuncio.created_at.desc()).limit(3).all())
    return render_template('student/dashboard.html',
                           user=user, periodo=periodo,
                           horario=horario, bloques=bloques,
                           inscripciones=inscripciones,
                           tramites=tramites, anuncios=anuncios,
                           today=datetime.utcnow().date())


@bp.get('/horario')
def horario_constructor():
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    periodo = PeriodoAcademico.query.filter_by(activo=True).first()
    horario = (Horario.query.filter(Horario.user_id == user.id,
                                    Horario.deleted_at.is_(None))
               .order_by(Horario.updated_at.desc()).first())
    return render_template('student/horario.html',
                           user=user, periodo=periodo, horario=horario)


@bp.get('/tramites')
def tramites():
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    items = (Tramite.query.filter_by(solicitante_id=user.id)
             .order_by(Tramite.created_at.desc()).all())
    tipos = TipoTramite.query.filter_by(activo=True).all()
    return render_template('student/tramites.html',
                           user=user, tramites=items, tipos=tipos)


@bp.get('/tramites/<int:t_id>')
def tramite_detalle(t_id):
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    from app.models import Tramite as TramiteM, SeguimientoTramite
    tramite = TramiteM.query.get_or_404(t_id)
    is_admin = user.rol in ('admin', 'coordinador', 'director', 'rector')
    if tramite.solicitante_id != user.id and not is_admin:
        return redirect(url_for('web_student.tramites'))
    seguimiento = (SeguimientoTramite.query
                   .filter_by(tramite_id=t_id)
                   .order_by(SeguimientoTramite.created_at).all())
    return render_template('student/tramite_detalle.html',
                           user=user, tramite=tramite,
                           seguimiento=seguimiento)


@bp.get('/inscripciones')
def inscripciones():
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    periodo = PeriodoAcademico.query.filter_by(activo=True).first()
    return render_template('student/inscripciones.html',
                           user=user, periodo=periodo)


@bp.get('/perfil')
def perfil():
    user = _require_login()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('student/perfil.html', user=user)
