"""Modelos de Matute Guide. Importados aquí para que Flask-Migrate los detecte."""
from app.models.usuarios import Plantel, User, RefreshToken, AuditLog
from app.models.academico import (
    Carrera, Materia, PeriodoAcademico, CalendarioAcademico,
)
from app.models.campus import Edificio, Salon, PuntoInteres
from app.models.horarios import Horario, Bloque, PlantillaHorario
from app.models.inscripciones import Inscripcion, Calificacion, RegistroAsistencia
from app.models.tramites import TipoTramite, Tramite, SeguimientoTramite
from app.models.notificaciones import Notificacion, Anuncio

__all__ = [
    'Plantel', 'User', 'RefreshToken', 'AuditLog',
    'Carrera', 'Materia', 'PeriodoAcademico', 'CalendarioAcademico',
    'Edificio', 'Salon', 'PuntoInteres',
    'Horario', 'Bloque', 'PlantillaHorario',
    'Inscripcion', 'Calificacion', 'RegistroAsistencia',
    'TipoTramite', 'Tramite', 'SeguimientoTramite',
    'Notificacion', 'Anuncio',
]
