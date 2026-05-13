"""Fixtures pytest. Cada test corre con BD en memoria poblada con seed mínimo."""
import os
import sys
import pytest

# Asegurar que el root del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    Plantel, User, Carrera, PeriodoAcademico, Edificio, Salon,
    Materia, Horario, Bloque,
)
from datetime import date, datetime, time


@pytest.fixture(scope='function')
def app():
    """App Flask en modo pruebas con BD SQLite en memoria."""
    os.environ['FLASK_CONFIG'] = 'pruebas'
    flask_app = create_app('pruebas')
    with flask_app.app_context():
        db.create_all()
        _seed_minimo()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """HTTP client del Flask app."""
    return app.test_client()


@pytest.fixture
def admin_token(client):
    res = client.post('/auth/login', json={
        'email': 'admin@test.mx', 'password': 'Admin1234!',
    })
    assert res.status_code == 200, res.get_json()
    return res.get_json()['access_token']


@pytest.fixture
def estudiante_token(client):
    res = client.post('/auth/login', json={
        'email': 'estudiante@test.mx', 'password': 'Estudiante1!',
    })
    assert res.status_code == 200, res.get_json()
    return res.get_json()['access_token']


def _seed_minimo():
    """Seed mínimo necesario para los tests: 1 plantel, 1 carrera,
    1 admin, 1 estudiante, 1 edificio + salón, 1 periodo activo,
    1 materia, 1 horario con conflicto."""
    plantel = Plantel(nombre='CUValles Test', clave='CUV-T', ciudad='Ameca')
    db.session.add(plantel); db.session.flush()

    carrera = Carrera(nombre='Test Informática', slug='test-inf',
                      plantel_id=plantel.id, activa=True)
    db.session.add(carrera); db.session.flush()

    admin = User(nombre='Admin', apellido_p='Test',
                 email='admin@test.mx', rol='admin',
                 plantel_id=plantel.id, estado='activo')
    admin.set_password('Admin1234!')
    db.session.add(admin)

    estud = User(nombre='Estu', apellido_p='Test',
                 email='estudiante@test.mx', rol='estudiante',
                 plantel_id=plantel.id, carrera_id=carrera.id,
                 semestre_actual=4, estado='activo')
    estud.set_password('Estudiante1!')
    db.session.add(estud); db.session.flush()

    edif = Edificio(plantel_id=plantel.id, nombre='Edif. T', clave='T',
                    activo=True)
    db.session.add(edif); db.session.flush()
    salon = Salon(edificio_id=edif.id, codigo='T-101', tipo='aula',
                  capacidad=30, activo=True)
    db.session.add(salon)

    periodo = PeriodoAcademico(clave='T-2026', plantel_id=plantel.id,
                               fecha_inicio=date(2026, 1, 1),
                               fecha_fin=date(2026, 6, 30), activo=True)
    db.session.add(periodo); db.session.flush()

    mat = Materia(clave='T-101', nombre='Materia Test',
                  carrera_id=carrera.id, semestre=4,
                  tipo='tronco_comun', creditos=8)
    db.session.add(mat); db.session.flush()

    h = Horario(user_id=estud.id, periodo_id=periodo.id,
                nombre='Horario Test', estado='publicado',
                publicado_at=datetime.utcnow())
    db.session.add(h); db.session.flush()

    # Dos bloques en el mismo día/hora → conflicto
    db.session.add(Bloque(horario_id=h.id, materia_id=mat.id,
                          salon_id=salon.id, dia='mie',
                          hora_inicio=time(11, 0), hora_fin=time(13, 0)))
    db.session.add(Bloque(horario_id=h.id, materia_id=mat.id,
                          salon_id=salon.id, dia='mie',
                          hora_inicio=time(11, 0), hora_fin=time(13, 0)))
    db.session.flush()

    from app.utils.conflicts import detectar_conflictos_horario
    detectar_conflictos_horario(h.id)
    db.session.commit()
