"""Mapa del campus."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.models import Edificio, PuntoInteres, Salon, Materia

bp = Blueprint('mapa_api', __name__)


@bp.get('')
def mapa():
    plantel_id = request.args.get('plantel_id')
    eq = Edificio.query.filter_by(activo=True)
    pq = PuntoInteres.query.filter_by(activo=True)
    if plantel_id:
        try:
            pid = int(plantel_id)
            eq = eq.filter_by(plantel_id=pid)
            pq = pq.filter_by(plantel_id=pid)
        except ValueError:
            pass
    return jsonify({
        'edificios': [{
            'id': e.id,
            'clave': e.clave,
            'nombre': e.nombre,
            'coordenadas_x': e.coordenadas_x,
            'coordenadas_y': e.coordenadas_y,
            'ancho': e.ancho_mapa,
            'alto': e.alto_mapa,
            'color': e.color_mapa,
        } for e in eq.all()],
        'puntos_interes': [p.to_dict() for p in pq.all()],
        'viewbox': {'x': 0, 'y': 0, 'w': 1200, 'h': 800},
    })


@bp.get('/ruta')
def ruta():
    origen = request.args.get('origen')
    destino = request.args.get('destino')
    if not (origen and destino):
        return jsonify({'error': 'origen y destino requeridos',
                        'code': 'MISSING_PARAMS'}), 422
    pasos = [
        f'Sal del punto de partida ({origen}).',
        'Camina por el andador principal hacia el norte.',
        f'El destino ({destino}) está a tu derecha.',
    ]
    return jsonify({'pasos': pasos, 'tiempo_estimado_min': 4})


@bp.get('/buscar')
@jwt_required()
def buscar():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'salones': [], 'edificios': [], 'materias': []})
    like = f'%{q}%'
    salones = Salon.query.filter(Salon.codigo.ilike(like) |
                                 Salon.nombre.ilike(like)).limit(8).all()
    edificios = Edificio.query.filter(Edificio.clave.ilike(like) |
                                      Edificio.nombre.ilike(like)).limit(5).all()
    materias = Materia.query.filter(Materia.nombre.ilike(like) |
                                    Materia.clave.ilike(like)).limit(8).all()
    return jsonify({
        'salones': [s.to_dict() for s in salones],
        'edificios': [e.to_dict() for e in edificios],
        'materias': [m.to_dict() for m in materias],
    })
