"""Vistas web del panel administrativo."""
from flask import Blueprint, render_template, redirect, url_for, session, request

from app.models import (
    User, Carrera, Materia, Salon, Edificio, Tramite,
    Anuncio, PeriodoAcademico, AuditLog, Plantel,
)

bp = Blueprint('web_admin', __name__)


def _require_admin():
    uid = session.get('user_id')
    if not uid:
        return None
    user = User.query.get(uid)
    if not user or user.is_deleted:
        return None
    if user.rol not in ('admin', 'director', 'coordinador', 'rector'):
        return None
    return user


@bp.get('')
@bp.get('/')
def admin_dashboard():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/dashboard.html', user=user)


@bp.get('/usuarios')
def usuarios():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/usuarios.html', user=user, rol_filtro=None)


@bp.get('/estudiantes')
def estudiantes():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/usuarios.html', user=user,
                           rol_filtro='estudiante')


@bp.get('/profesores')
def profesores():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/usuarios.html', user=user,
                           rol_filtro='profesor')


@bp.get('/horarios')
def horarios():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    carreras = Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).all()
    edificios = Edificio.query.filter_by(activo=True).all()
    profesores = User.query.filter_by(rol='profesor', estado='activo').filter(
        User.deleted_at.is_(None)).all()
    periodos = PeriodoAcademico.query.order_by(
        PeriodoAcademico.fecha_inicio.desc()).all()
    return render_template('admin/horarios.html',
                           user=user, carreras=carreras,
                           edificios=edificios, profesores=profesores,
                           periodos=periodos)


@bp.get('/salones')
def salones():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    edificios = Edificio.query.filter_by(activo=True).all()
    return render_template('admin/salones.html',
                           user=user, edificios=edificios)


@bp.get('/carreras')
def carreras():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/carreras.html', user=user)


@bp.get('/carreras/<int:carrera_id>')
def carrera_detalle(carrera_id):
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    from app.models import Carrera as CarreraM
    carrera = CarreraM.query.get_or_404(carrera_id)
    return render_template('admin/carrera_detalle.html',
                           user=user, carrera=carrera)


@bp.get('/horarios/plantillas')
def plantillas_horario():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    carreras_qs = (Carrera.query.filter_by(activa=True)
                   .filter(Carrera.deleted_at.is_(None)).all())
    return render_template('admin/plantillas.html',
                           user=user, carreras=carreras_qs)


@bp.get('/materias')
def materias():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    carreras_qs = Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).all()
    return render_template('admin/materias.html',
                           user=user, carreras=carreras_qs)


@bp.get('/periodos')
def periodos():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/periodos.html', user=user)


@bp.get('/tramites')
def tramites():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/tramites.html', user=user)


@bp.get('/anuncios')
def anuncios():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/anuncios.html', user=user)


@bp.get('/reportes')
def reportes():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/reportes.html', user=user)


@bp.get('/audit')
def audit():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    return render_template('admin/audit.html', user=user)


@bp.get('/configuracion')
def configuracion():
    user = _require_admin()
    if not user:
        return redirect(url_for('web_auth.login'))
    planteles = Plantel.query.filter_by(activo=True).all()
    return render_template('admin/configuracion.html',
                           user=user, planteles=planteles)
