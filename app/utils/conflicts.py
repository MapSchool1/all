"""Detección de conflictos en bloques de horario."""
from app.extensions import db
from app.models import Bloque


def _overlaps(a_inicio, a_fin, b_inicio, b_fin):
    return a_inicio < b_fin and b_inicio < a_fin


def detectar_conflictos_horario(horario_id):
    """Marca conflictos en TODOS los bloques de un horario.
    Devuelve lista de IDs en conflicto."""
    bloques = Bloque.query.filter_by(horario_id=horario_id).all()
    conflictos = {b.id: [] for b in bloques}
    for i, a in enumerate(bloques):
        for b in bloques[i + 1:]:
            if a.dia == b.dia and _overlaps(a.hora_inicio, a.hora_fin,
                                            b.hora_inicio, b.hora_fin):
                conflictos[a.id].append(b.id)
                conflictos[b.id].append(a.id)
    en_conflicto = []
    for b in bloques:
        b.conflicto = bool(conflictos[b.id])
        b.conflicto_con = conflictos[b.id] or None
        if b.conflicto:
            en_conflicto.append(b.id)

    horario = bloques[0].horario if bloques else None
    if horario:
        horario.tiene_conflictos = bool(en_conflicto)
    db.session.flush()
    return en_conflicto


def salon_disponible(salon_id, dia, hora_inicio, hora_fin, periodo_id,
                     excluir_bloque_id=None):
    """Devuelve True si el salón está libre. Considera bloques de horarios
    publicados del mismo periodo."""
    from app.models import Horario
    q = (Bloque.query
         .join(Horario, Horario.id == Bloque.horario_id)
         .filter(Bloque.salon_id == salon_id,
                 Bloque.dia == dia,
                 Horario.periodo_id == periodo_id,
                 Horario.estado == 'publicado',
                 Horario.deleted_at.is_(None)))
    if excluir_bloque_id:
        q = q.filter(Bloque.id != excluir_bloque_id)
    for b in q.all():
        if _overlaps(b.hora_inicio, b.hora_fin, hora_inicio, hora_fin):
            return False, b
    return True, None
