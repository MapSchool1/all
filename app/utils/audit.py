from flask import request
from app.extensions import db
from app.models import AuditLog


def write_audit(user_id, accion, entidad=None, entidad_id=None,
                payload_antes=None, payload_despues=None):
    """Crea un registro de auditoría. Llamar dentro de una transacción."""
    log = AuditLog(
        user_id=user_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        payload_antes=payload_antes,
        payload_despues=payload_despues,
        ip=request.remote_addr if request else None,
        user_agent=(request.headers.get('User-Agent', '')[:255]
                    if request else None),
    )
    db.session.add(log)
    return log
