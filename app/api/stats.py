"""Estadísticas y dashboards."""
import csv
import io
from datetime import datetime, timedelta, date
from collections import defaultdict
from flask import Blueprint, jsonify, request, Response

from app.extensions import db
from app.models import (
    User, Horario, Bloque, Tramite, Carrera, Salon,
    RegistroAsistencia, Calificacion, Inscripcion,
)
from app.utils.decorators import roles_required

bp = Blueprint('stats_api', __name__)


def _csv_response(rows, headers, filename):
    """Genera una respuesta CSV con BOM para Excel."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    csv_text = '﻿' + buf.getvalue()
    return Response(
        csv_text,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@bp.get('/dashboard')
@roles_required('admin', 'director', 'coordinador', 'rector')
def dashboard():
    week_ago = datetime.utcnow() - timedelta(days=7)
    today_start = datetime.combine(date.today(), datetime.min.time())

    estudiantes = User.query.filter(User.rol == 'estudiante',
                                    User.estado == 'activo',
                                    User.deleted_at.is_(None)).count()
    estudiantes_prev = User.query.filter(User.rol == 'estudiante',
                                         User.created_at < week_ago,
                                         User.deleted_at.is_(None)).count()
    delta_est = round(((estudiantes - estudiantes_prev) /
                       estudiantes_prev * 100), 1) if estudiantes_prev else 0

    horarios_pub = Horario.query.filter_by(estado='publicado').filter(
        Horario.deleted_at.is_(None)).count()
    horarios_meta = max(estudiantes // 50 * 50, 50)
    horarios_pub_week = Horario.query.filter(
        Horario.estado == 'publicado',
        Horario.publicado_at >= week_ago,
        Horario.deleted_at.is_(None)).count()

    conflictos = (db.session.query(Horario)
                  .filter(Horario.tiene_conflictos.is_(True),
                          Horario.deleted_at.is_(None)).count())

    asist_query = RegistroAsistencia.query.all()
    if asist_query:
        pres = sum(1 for r in asist_query if r.estado in ('presente', 'justificado'))
        asist_prom = round(pres / len(asist_query) * 100, 1)
    else:
        asist_prom = 0

    tramites_pendientes = Tramite.query.filter(Tramite.estado.in_(
        ('recibido', 'en_proceso', 'pendiente_pago'))).count()

    nuevos_users_hoy = User.query.filter(
        User.created_at >= today_start,
        User.deleted_at.is_(None)).count()
    nuevos_tramites_hoy = Tramite.query.filter(
        Tramite.created_at >= today_start).count()

    return jsonify({
        'estudiantes_activos': {
            'total': estudiantes, 'delta': delta_est,
            'periodo': 'vs sem. anterior',
        },
        'horarios_publicados': {
            'total': horarios_pub, 'meta': horarios_meta,
            'delta': horarios_pub_week, 'periodo': 'esta semana',
        },
        'conflictos_abiertos': {
            'total': conflictos, 'delta': 0, 'periodo': 'vigentes',
        },
        'asistencia_promedio': {
            'valor': asist_prom, 'delta': 0, 'periodo': 'global',
        },
        'tramites_pendientes': {'total': tramites_pendientes},
        'nuevos_hoy': {'usuarios': nuevos_users_hoy,
                       'tramites': nuevos_tramites_hoy},
    })


@bp.get('/dashboard/publico')
def dashboard_publico():
    """Stats públicos para landing page."""
    estudiantes = User.query.filter(User.rol == 'estudiante',
                                    User.estado == 'activo',
                                    User.deleted_at.is_(None)).count()
    horarios = Horario.query.filter_by(estado='publicado').filter(
        Horario.deleted_at.is_(None)).count()
    salones = Salon.query.filter_by(activo=True).filter(
        Salon.deleted_at.is_(None)).count()
    carreras = Carrera.query.filter_by(activa=True).filter(
        Carrera.deleted_at.is_(None)).count()
    return jsonify({
        'estudiantes': estudiantes,
        'horarios': horarios,
        'salones': salones,
        'carreras': carreras,
    })


@bp.get('/usuarios')
@roles_required('admin', 'director', 'rector')
def stats_usuarios():
    por_rol = defaultdict(int)
    por_estado = defaultdict(int)
    for u in User.query.filter(User.deleted_at.is_(None)).all():
        por_rol[u.rol] += 1
        por_estado[u.estado] += 1
    days = int(request.args.get('periodo', '30').replace('d', '').replace('y', '365'))
    cutoff = datetime.utcnow() - timedelta(days=days)
    nuevos = (User.query.filter(User.created_at >= cutoff,
                                User.deleted_at.is_(None)).all())
    por_dia = defaultdict(int)
    for u in nuevos:
        por_dia[u.created_at.date().isoformat()] += 1
    return jsonify({
        'por_rol': dict(por_rol),
        'por_estado': dict(por_estado),
        'nuevos_por_dia': sorted(por_dia.items()),
    })


@bp.get('/salones')
@roles_required('admin', 'coordinador', 'director', 'rector')
def stats_salones():
    salones = Salon.query.filter(Salon.deleted_at.is_(None)).all()
    por_tipo = defaultdict(int)
    for s in salones:
        por_tipo[s.tipo or 'otro'] += 1
    uso = defaultdict(int)
    for b in Bloque.query.all():
        if b.salon_id:
            uso[b.salon_id] += 1
    mas_usados = sorted(uso.items(), key=lambda x: -x[1])[:5]
    salones_dict = {s.id: s.codigo for s in salones}
    return jsonify({
        'total': len(salones),
        'por_tipo': dict(por_tipo),
        'mas_usados': [{'salon': salones_dict.get(sid, '?'), 'bloques': n}
                       for sid, n in mas_usados],
    })


@bp.get('/carreras')
@roles_required('admin', 'director', 'rector')
def stats_carreras():
    out = []
    for c in Carrera.query.filter_by(activa=True).filter(
            Carrera.deleted_at.is_(None)).all():
        est = User.query.filter_by(carrera_id=c.id, rol='estudiante',
                                   estado='activo').filter(
            User.deleted_at.is_(None)).count()
        horarios = (Horario.query.join(User, User.id == Horario.user_id)
                    .filter(User.carrera_id == c.id,
                            Horario.estado == 'publicado',
                            Horario.deleted_at.is_(None)).count())
        out.append({
            'id': c.id, 'nombre': c.nombre,
            'estudiantes': est,
            'horarios_pub': horarios,
            'asistencia_prom': None,
        })
    return jsonify({'carreras': out})


@bp.get('/asistencia')
@roles_required('coordinador', 'admin', 'director')
def stats_asistencia():
    regs = RegistroAsistencia.query.all()
    total = len(regs) or 1
    pres = sum(1 for r in regs if r.estado == 'presente')
    just = sum(1 for r in regs if r.estado == 'justificado')
    aus = sum(1 for r in regs if r.estado == 'ausente')
    return jsonify({
        'promedio': round((pres + just) / total * 100, 1),
        'distribucion': {
            'presente': pres, 'justificado': just, 'ausente': aus,
            'retardo': sum(1 for r in regs if r.estado == 'retardo'),
        },
    })


@bp.get('/calificaciones')
@roles_required('coordinador', 'admin', 'director')
def stats_calificaciones():
    califs = Calificacion.query.filter(
        Calificacion.valor.isnot(None)).all()
    if not califs:
        return jsonify({
            'distribucion_notas': {},
            'aprobacion_pct': 0, 'reprobacion_pct': 0,
        })
    bins = {'<6': 0, '6-7': 0, '7-8': 0, '8-9': 0, '9-10': 0}
    aprob = 0
    for c in califs:
        v = float(c.valor)
        if v < 6:
            bins['<6'] += 1
        elif v < 7:
            bins['6-7'] += 1
            aprob += 1
        elif v < 8:
            bins['7-8'] += 1
            aprob += 1
        elif v < 9:
            bins['8-9'] += 1
            aprob += 1
        else:
            bins['9-10'] += 1
            aprob += 1
    return jsonify({
        'distribucion_notas': bins,
        'aprobacion_pct': round(aprob / len(califs) * 100, 1),
        'reprobacion_pct': round((len(califs) - aprob) / len(califs) * 100, 1),
    })


# =============== EXPORT CSV ===============

@bp.get('/export/usuarios.csv')
@roles_required('admin', 'director', 'rector')
def export_usuarios():
    rows = []
    for u in User.query.filter(User.deleted_at.is_(None)).order_by(
            User.created_at.desc()).all():
        rows.append([
            u.id, u.expediente or '', u.nombre_completo, u.email,
            u.rol, u.estado,
            u.plantel.clave if u.plantel else '',
            u.semestre_actual or '',
            u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '',
            u.ultimo_acceso.strftime('%Y-%m-%d %H:%M') if u.ultimo_acceso else '',
        ])
    return _csv_response(
        rows,
        ['ID', 'Expediente', 'Nombre completo', 'Email', 'Rol', 'Estado',
         'Plantel', 'Semestre', 'Creado', 'Último acceso'],
        f'usuarios-{datetime.utcnow().strftime("%Y%m%d")}.csv',
    )


@bp.get('/export/salones.csv')
@roles_required('admin', 'coordinador', 'director', 'rector')
def export_salones():
    rows = []
    for s in Salon.query.filter(Salon.deleted_at.is_(None)).order_by(
            Salon.codigo).all():
        rows.append([
            s.id, s.codigo, s.nombre or '',
            s.edificio.clave if s.edificio else '',
            s.tipo or '', s.capacidad, s.piso,
            ', '.join(s.equipamiento or []) if s.equipamiento else '',
            'Sí' if s.activo else 'No',
        ])
    return _csv_response(
        rows,
        ['ID', 'Código', 'Nombre', 'Edificio', 'Tipo', 'Capacidad', 'Piso',
         'Equipamiento', 'Activo'],
        f'salones-{datetime.utcnow().strftime("%Y%m%d")}.csv',
    )


@bp.get('/export/asistencia.csv')
@roles_required('coordinador', 'admin', 'director')
def export_asistencia():
    rows = []
    for r in RegistroAsistencia.query.order_by(
            RegistroAsistencia.fecha.desc()).all():
        ins = r.inscripcion
        rows.append([
            r.fecha.isoformat() if r.fecha else '',
            ins.estudiante.nombre_completo if ins and ins.estudiante else '',
            ins.estudiante.expediente if ins and ins.estudiante else '',
            ins.materia.clave if ins and ins.materia else '',
            ins.materia.nombre if ins and ins.materia else '',
            r.estado,
            r.justificacion or '',
        ])
    return _csv_response(
        rows,
        ['Fecha', 'Estudiante', 'Expediente', 'Clave materia', 'Materia',
         'Estado', 'Justificación'],
        f'asistencia-{datetime.utcnow().strftime("%Y%m%d")}.csv',
    )


@bp.get('/export/calificaciones.csv')
@roles_required('coordinador', 'admin', 'director')
def export_calificaciones():
    rows = []
    for c in Calificacion.query.order_by(Calificacion.capturado_at.desc()).all():
        ins = c.inscripcion
        rows.append([
            c.id, ins.estudiante.expediente if ins and ins.estudiante else '',
            ins.estudiante.nombre_completo if ins and ins.estudiante else '',
            ins.materia.clave if ins and ins.materia else '',
            ins.materia.nombre if ins and ins.materia else '',
            c.tipo,
            float(c.valor) if c.valor is not None else '',
            'Sí' if c.publicado else 'No',
            c.capturado_at.strftime('%Y-%m-%d %H:%M') if c.capturado_at else '',
        ])
    return _csv_response(
        rows,
        ['ID', 'Expediente', 'Estudiante', 'Clave materia', 'Materia',
         'Tipo', 'Valor', 'Publicada', 'Capturada'],
        f'calificaciones-{datetime.utcnow().strftime("%Y%m%d")}.csv',
    )


@bp.get('/export/tramites.csv')
@roles_required('admin', 'coordinador', 'director')
def export_tramites():
    rows = []
    for t in Tramite.query.order_by(Tramite.created_at.desc()).all():
        rows.append([
            t.folio,
            t.solicitante.nombre_completo if t.solicitante else '',
            t.solicitante.email if t.solicitante else '',
            t.tipo_tramite.nombre if t.tipo_tramite else '',
            t.estado,
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
            t.entregado_at.strftime('%Y-%m-%d %H:%M') if t.entregado_at else '',
            (t.descripcion or '')[:200],
        ])
    return _csv_response(
        rows,
        ['Folio', 'Solicitante', 'Email', 'Tipo', 'Estado', 'Solicitado',
         'Entregado', 'Descripción'],
        f'tramites-{datetime.utcnow().strftime("%Y%m%d")}.csv',
    )
