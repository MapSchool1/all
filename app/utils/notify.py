from app.extensions import db
from app.models import Notificacion


def notify(user_id, tipo, titulo, cuerpo=None, accion_url=None, metadata=None,
           commit=True):
    """Crea una notificación para un usuario."""
    n = Notificacion(
        destinatario_id=user_id,
        tipo=tipo,
        titulo=titulo,
        cuerpo=cuerpo,
        accion_url=accion_url,
        extra=metadata,
    )
    db.session.add(n)
    if commit:
        db.session.commit()
    return n
