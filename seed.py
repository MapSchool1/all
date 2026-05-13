"""Población inicial de la base de datos con datos realistas."""
import os
from datetime import datetime, date, timedelta, time

from app import create_app
from app.extensions import db
from app.models import (
    Plantel, User, Carrera, Materia, PeriodoAcademico, CalendarioAcademico,
    Edificio, Salon, PuntoInteres, Horario, Bloque, Inscripcion, Calificacion,
    RegistroAsistencia, TipoTramite, Tramite, SeguimientoTramite,
    Notificacion, Anuncio,
)


# ============== DATOS BASE ==============

PLANTELES_DATA = [
    {'nombre': 'CUValles', 'clave': 'CUV', 'ciudad': 'Ameca, Jalisco',
     'direccion': 'Carretera Guadalajara–Ameca km. 45.5'},
]

CARRERAS_DATA = [
    {'nombre': 'Tecnólogo Profesional en Informática',
     'nombre_corto': 'Tec. Informática', 'slug': 'tec-informatica',
     'descripcion': 'Forma profesionales en desarrollo de software, '
                    'soporte técnico, redes y sistemas de información.',
     'campos': 'desarrollo, soporte, redes y datos',
     'duracion_semestres': 8, 'creditos_totales': 320},
    {'nombre': 'Tecnólogo Profesional en Biotecnología',
     'nombre_corto': 'Tec. Biotecnología', 'slug': 'tec-biotecnologia',
     'descripcion': 'Aplicación de procesos biológicos para la industria '
                    'agroalimentaria, salud y medio ambiente.',
     'campos': 'laboratorio, agroindustria, salud',
     'duracion_semestres': 8, 'creditos_totales': 320},
    {'nombre': 'Tecnólogo Profesional en Energías Alternas',
     'nombre_corto': 'Tec. Energías', 'slug': 'tec-energias',
     'descripcion': 'Diseño e implementación de soluciones de energía '
                    'solar, eólica y eficiencia energética.',
     'campos': 'solar, eólica, eficiencia energética',
     'duracion_semestres': 8, 'creditos_totales': 320},
]

EDIFICIOS_DATA = [
    {'clave': 'A', 'nombre': 'Edificio A — Aulas',
     'descripcion': 'Aulas teóricas y oficinas administrativas.',
     'coordenadas_x': 120, 'coordenadas_y': 180,
     'ancho_mapa': 220, 'alto_mapa': 140, 'salones': 15},
    {'clave': 'B', 'nombre': 'Edificio B — Aulas',
     'descripcion': 'Aulas teóricas, segundo bloque.',
     'coordenadas_x': 380, 'coordenadas_y': 180,
     'ancho_mapa': 200, 'alto_mapa': 140, 'salones': 10},
    {'clave': 'C', 'nombre': 'Edificio C — Aulas y Auditorio',
     'descripcion': 'Aulas y auditorio principal.',
     'coordenadas_x': 620, 'coordenadas_y': 180,
     'ancho_mapa': 200, 'alto_mapa': 140, 'salones': 8},
    {'clave': 'CELE', 'nombre': 'Centro de Lenguas Extranjeras',
     'descripcion': 'Salones de idiomas y biblioteca multimedia.',
     'coordenadas_x': 120, 'coordenadas_y': 460,
     'ancho_mapa': 220, 'alto_mapa': 130, 'salones': 6,
     'color_mapa': '#3C61A5'},
    {'clave': 'LAB', 'nombre': 'Laboratorios',
     'descripcion': 'Laboratorios de cómputo, redes y biotecnología.',
     'coordenadas_x': 380, 'coordenadas_y': 460,
     'ancho_mapa': 220, 'alto_mapa': 130, 'salones': 5,
     'color_mapa': '#28A745'},
]

POI_DATA = [
    {'nombre': 'Cafetería principal', 'tipo': 'cafeteria',
     'coord_x': 760, 'coord_y': 400, 'icono': 'coffee',
     'descripcion': 'Lunes a viernes, 7:00 a 18:00 h.'},
    {'nombre': 'Biblioteca central', 'tipo': 'biblioteca',
     'coord_x': 280, 'coord_y': 360, 'icono': 'book',
     'descripcion': 'Acervo físico y digital. Salas de estudio.'},
    {'nombre': 'Enfermería', 'tipo': 'enfermeria',
     'coord_x': 880, 'coord_y': 280, 'icono': 'plus',
     'descripcion': 'Atención de primer contacto.'},
    {'nombre': 'Estacionamiento norte', 'tipo': 'estacionamiento',
     'coord_x': 480, 'coord_y': 60, 'icono': 'car'},
    {'nombre': 'Canchas deportivas', 'tipo': 'canchas',
     'coord_x': 880, 'coord_y': 540, 'icono': 'flag'},
    {'nombre': 'Sanitarios A', 'tipo': 'bano',
     'coord_x': 240, 'coord_y': 240, 'icono': 'square'},
]

USERS_DATA = [
    {'nombre': 'Diego', 'apellido_p': 'Hernández', 'apellido_m': 'Romero',
     'email': 'admin@udg.mx', 'rol': 'admin',
     'expediente': 'A-001', 'avatar_color': '#172846',
     'password': 'Admin1234!'},
    {'nombre': 'Cristina', 'apellido_p': 'Aguirre', 'apellido_m': 'Solís',
     'email': 'cristina.aguirre@udg.mx', 'rol': 'director',
     'expediente': 'D-001', 'password': 'Director1!'},
    {'nombre': 'Álvaro', 'apellido_p': 'Díaz', 'apellido_m': 'Ramírez',
     'email': 'alvaro.diaz@alumnos.udg.mx', 'rol': 'estudiante',
     'expediente': '218 492', 'semestre_actual': 4,
     'carrera_slug': 'tec-informatica',
     'avatar_color': '#3C61A5', 'password': 'Estudiante1!'},
    {'nombre': 'Yael Omar', 'apellido_p': 'Vega', 'apellido_m': 'Cruz',
     'email': 'yael.vega@alumnos.udg.mx', 'rol': 'estudiante',
     'expediente': '218 731', 'semestre_actual': 2,
     'carrera_slug': 'tec-biotecnologia',
     'avatar_color': '#28A745', 'password': 'Estudiante1!'},
    {'nombre': 'Rocío', 'apellido_p': 'Castellanos', 'apellido_m': 'Pérez',
     'email': 'rocio.castellanos@alumnos.udg.mx', 'rol': 'estudiante',
     'expediente': '218 902', 'semestre_actual': 6,
     'carrera_slug': 'tec-energias',
     'avatar_color': '#F2B705', 'password': 'Estudiante1!'},
    {'nombre': 'Jorge', 'apellido_p': 'Méndez', 'apellido_m': 'García',
     'email': 'jorge.mendez@udg.mx', 'rol': 'profesor',
     'expediente': 'P-218', 'avatar_color': '#233C5B',
     'password': 'Profesor1!'},
    {'nombre': 'Laura', 'apellido_p': 'López', 'apellido_m': 'Vargas',
     'email': 'laura.lopez@udg.mx', 'rol': 'profesor',
     'expediente': 'P-219', 'avatar_color': '#0D6EFD',
     'password': 'Profesor1!'},
    {'nombre': 'Andrea', 'apellido_p': 'Reyes', 'apellido_m': 'Torres',
     'email': 'andrea.reyes@udg.mx', 'rol': 'profesor',
     'expediente': 'P-220', 'password': 'Profesor1!'},
    {'nombre': 'Patricia', 'apellido_p': 'Torres', 'apellido_m': 'Mejía',
     'email': 'patricia.torres@udg.mx', 'rol': 'profesor',
     'expediente': 'P-221', 'password': 'Profesor1!'},
    {'nombre': 'Roberto', 'apellido_p': 'Brown', 'apellido_m': 'Cabrera',
     'email': 'roberto.brown@udg.mx', 'rol': 'profesor',
     'expediente': 'P-222', 'password': 'Profesor1!'},
    {'nombre': 'Estela', 'apellido_p': 'Vargas', 'apellido_m': 'Núñez',
     'email': 'estela.vargas@udg.mx', 'rol': 'profesor',
     'expediente': 'P-223', 'password': 'Profesor1!'},
    {'nombre': 'Coordinador', 'apellido_p': 'Académico', 'apellido_m': 'CUV',
     'email': 'coordinador@udg.mx', 'rol': 'coordinador',
     'expediente': 'C-001', 'password': 'Coordinador1!'},
]

TIPOS_TRAMITE_DATA = [
    {'nombre': 'Constancia de estudios',
     'descripcion': 'Documento oficial que acredita tu inscripción.',
     'requiere_documentos': ['Identificación oficial'],
     'costo': 0, 'tiempo_estimado_dias': 3},
    {'nombre': 'Kárdex con calificaciones',
     'descripcion': 'Historial académico con calificaciones por semestre.',
     'requiere_documentos': ['Identificación oficial'],
     'costo': 50, 'tiempo_estimado_dias': 5},
    {'nombre': 'Constancia con horario',
     'descripcion': 'Constancia de inscripción con horario detallado.',
     'requiere_documentos': ['Identificación oficial'],
     'costo': 0, 'tiempo_estimado_dias': 2},
    {'nombre': 'Reposición de credencial',
     'descripcion': 'Solicita una nueva credencial estudiantil.',
     'requiere_documentos': ['Identificación oficial', 'Reporte si fue extravío'],
     'costo': 120, 'tiempo_estimado_dias': 10},
    {'nombre': 'Baja temporal',
     'descripcion': 'Suspensión temporal de tus estudios.',
     'requiere_documentos': ['Identificación oficial', 'Carta de motivos'],
     'costo': 0, 'tiempo_estimado_dias': 7},
]


# ============== MATERIAS POR CARRERA Y SEMESTRE ==============

MATERIAS_PLAN = {
    'tec-informatica': {
        1: [('INF-101', 'Fundamentos de Programación', 'tronco_comun', 8),
            ('INF-102', 'Álgebra Lineal', 'tronco_comun', 6),
            ('INF-103', 'Introducción a la Computación', 'tronco_comun', 6),
            ('INF-104', 'Inglés I', 'idiomas', 4),
            ('INF-105', 'Comunicación Académica', 'tronco_comun', 4),
            ('INF-106', 'Lab. de Programación', 'laboratorio', 4)],
        2: [('INF-201', 'Programación Orientada a Objetos', 'area_profesional', 8),
            ('INF-202', 'Cálculo Diferencial', 'tronco_comun', 6),
            ('INF-203', 'Estructura de Datos', 'area_profesional', 6),
            ('INF-204', 'Inglés II', 'idiomas', 4),
            ('INF-205', 'Lab. de POO', 'laboratorio', 4),
            ('INF-206', 'Sistemas Operativos', 'area_profesional', 6)],
        3: [('INF-301', 'Bases de Datos', 'area_profesional', 8),
            ('INF-302', 'Cálculo Integral', 'tronco_comun', 6),
            ('INF-303', 'Redes de Computadoras I', 'area_profesional', 6),
            ('INF-304', 'Inglés III', 'idiomas', 4),
            ('INF-305', 'Lab. de Redes', 'laboratorio', 4),
            ('INF-306', 'Algoritmos Avanzados', 'area_profesional', 6)],
        4: [('INF-401', 'Cálculo I', 'tronco_comun', 8),
            ('INF-402', 'Tecnología en la Contabilidad', 'area_profesional', 6),
            ('INF-403', 'Programación Web', 'area_profesional', 6),
            ('INF-404', 'Bases de Datos II', 'area_profesional', 6),
            ('INF-405', 'Inglés VII', 'idiomas', 4),
            ('INF-406', 'Estadística Descriptiva', 'tronco_comun', 6)],
    },
    'tec-biotecnologia': {
        1: [('BIO-101', 'Química General', 'tronco_comun', 8),
            ('BIO-102', 'Biología Celular', 'tronco_comun', 6),
            ('BIO-103', 'Matemáticas Básicas', 'tronco_comun', 6),
            ('BIO-104', 'Inglés I', 'idiomas', 4),
            ('BIO-105', 'Lab. de Química', 'laboratorio', 4),
            ('BIO-106', 'Introducción a la Biotecnología', 'tronco_comun', 4)],
        2: [('BIO-201', 'Bioquímica', 'area_profesional', 8),
            ('BIO-202', 'Microbiología', 'area_profesional', 6),
            ('BIO-203', 'Genética General', 'area_profesional', 6),
            ('BIO-204', 'Inglés II', 'idiomas', 4),
            ('BIO-205', 'Lab. de Microbiología', 'laboratorio', 4),
            ('BIO-206', 'Estadística Aplicada', 'tronco_comun', 6)],
        3: [('BIO-301', 'Biología Molecular', 'area_profesional', 8),
            ('BIO-302', 'Bioprocesos I', 'area_profesional', 6),
            ('BIO-303', 'Inmunología', 'area_profesional', 6),
            ('BIO-304', 'Inglés III', 'idiomas', 4),
            ('BIO-305', 'Lab. de Bioquímica', 'laboratorio', 4),
            ('BIO-306', 'Bioética', 'tronco_comun', 4)],
        4: [('BIO-401', 'Biotecnología Vegetal', 'area_profesional', 8),
            ('BIO-402', 'Biotecnología Animal', 'area_profesional', 6),
            ('BIO-403', 'Bioprocesos II', 'area_profesional', 6),
            ('BIO-404', 'Inglés IV', 'idiomas', 4),
            ('BIO-405', 'Lab. de Bioprocesos', 'laboratorio', 4),
            ('BIO-406', 'Gestión de la Calidad', 'tronco_comun', 6)],
    },
    'tec-energias': {
        1: [('ENE-101', 'Física Mecánica', 'tronco_comun', 8),
            ('ENE-102', 'Cálculo Diferencial', 'tronco_comun', 6),
            ('ENE-103', 'Química General', 'tronco_comun', 6),
            ('ENE-104', 'Inglés I', 'idiomas', 4),
            ('ENE-105', 'Dibujo Técnico', 'area_profesional', 4),
            ('ENE-106', 'Intro. a Energías Renovables', 'tronco_comun', 4)],
        2: [('ENE-201', 'Termodinámica', 'area_profesional', 8),
            ('ENE-202', 'Electricidad y Magnetismo', 'area_profesional', 6),
            ('ENE-203', 'Cálculo Integral', 'tronco_comun', 6),
            ('ENE-204', 'Inglés II', 'idiomas', 4),
            ('ENE-205', 'Lab. de Física', 'laboratorio', 4),
            ('ENE-206', 'Materiales para Energía', 'area_profesional', 6)],
        3: [('ENE-301', 'Energía Solar Fotovoltaica', 'area_profesional', 8),
            ('ENE-302', 'Mecánica de Fluidos', 'area_profesional', 6),
            ('ENE-303', 'Circuitos Eléctricos', 'area_profesional', 6),
            ('ENE-304', 'Inglés III', 'idiomas', 4),
            ('ENE-305', 'Lab. de Solar', 'laboratorio', 4),
            ('ENE-306', 'Eficiencia Energética', 'area_profesional', 6)],
        4: [('ENE-401', 'Energía Eólica', 'area_profesional', 8),
            ('ENE-402', 'Sistemas de Almacenamiento', 'area_profesional', 6),
            ('ENE-403', 'Smart Grids', 'area_profesional', 6),
            ('ENE-404', 'Inglés IV', 'idiomas', 4),
            ('ENE-405', 'Lab. de Eólica', 'laboratorio', 4),
            ('ENE-406', 'Gestión de Proyectos', 'tronco_comun', 6)],
    },
}


# ============== HORARIO DE ÁLVARO (con conflicto Mié 11:00) ==============

ALVARO_BLOQUES = [
    # día, hora_inicio, hora_fin, materia_clave, salon_codigo, profesor_email
    ('lun', '07:00', '09:00', 'INF-401', 'A-203', 'jorge.mendez@udg.mx'),
    ('lun', '09:00', '11:00', 'INF-402', 'B-105', 'laura.lopez@udg.mx'),
    ('mar', '09:00', '11:00', 'INF-402', 'B-105', 'laura.lopez@udg.mx'),
    ('mar', '11:00', '13:00', 'INF-403', 'LAB-4', 'andrea.reyes@udg.mx'),
    ('mar', '15:00', '17:00', 'INF-406', 'A-105', 'estela.vargas@udg.mx'),
    ('mie', '07:00', '09:00', 'INF-401', 'A-203', 'jorge.mendez@udg.mx'),
    ('mie', '11:00', '13:00', 'INF-403', 'LAB-4', 'andrea.reyes@udg.mx'),
    ('mie', '11:00', '13:00', 'INF-404', 'LAB-2', 'patricia.torres@udg.mx'),  # CONFLICTO
    ('jue', '09:00', '11:00', 'INF-402', 'B-105', 'laura.lopez@udg.mx'),
    ('jue', '13:00', '15:00', 'INF-405', 'CELE-2', 'roberto.brown@udg.mx'),
    ('jue', '15:00', '17:00', 'INF-406', 'A-105', 'estela.vargas@udg.mx'),
    ('vie', '07:00', '09:00', 'INF-401', 'A-203', 'jorge.mendez@udg.mx'),
    ('vie', '13:00', '15:00', 'INF-405', 'CELE-2', 'roberto.brown@udg.mx'),
]


# ============== EJECUTAR ==============

def crear_salones(edificio, total):
    """Genera salones para un edificio según su clave."""
    out = []
    if edificio.clave == 'CELE':
        for i in range(1, total + 1):
            out.append(Salon(
                edificio_id=edificio.id,
                codigo=f'CELE-{i}',
                nombre=f'Sala de idiomas {i}',
                tipo='sala_idiomas', capacidad=24,
                piso=1 + (i - 1) // 4,
                equipamiento=['proyector', 'AC', 'pizarrón_digital'],
                coord_x=20 + ((i - 1) % 4) * 45,
                coord_y=20 + ((i - 1) // 4) * 50,
            ))
    elif edificio.clave == 'LAB':
        labs = [('LAB-1', 'Lab. de Química', 'laboratorio', 24),
                ('LAB-2', 'Lab. de Bases de Datos', 'sala_computo', 30),
                ('LAB-3', 'Lab. de Redes', 'laboratorio', 24),
                ('LAB-4', 'Lab. de Programación Web', 'sala_computo', 30),
                ('LAB-5', 'Lab. de Biotecnología', 'laboratorio', 20)]
        for i, (cod, nom, tipo, cap) in enumerate(labs):
            out.append(Salon(
                edificio_id=edificio.id, codigo=cod, nombre=nom,
                tipo=tipo, capacidad=cap, piso=1,
                equipamiento=['proyector', 'AC', 'pizarrón',
                              'equipo especializado'],
                coord_x=20 + (i % 3) * 60,
                coord_y=20 + (i // 3) * 60,
            ))
    elif edificio.clave == 'C':
        # Auditorio + 7 aulas
        out.append(Salon(
            edificio_id=edificio.id, codigo='C-AUD',
            nombre='Auditorio principal',
            tipo='auditorio', capacidad=180, piso=1,
            equipamiento=['proyector', 'AC', 'micrófonos', 'pizarrón'],
            coord_x=20, coord_y=20,
        ))
        for i in range(1, total):
            piso = (i + 1) // 4 + 1
            num = 100 * piso + i
            out.append(Salon(
                edificio_id=edificio.id,
                codigo=f'C-{num}', nombre=f'Aula C-{num}',
                tipo='aula', capacidad=40, piso=piso,
                equipamiento=['proyector', 'AC', 'pizarrón'],
                coord_x=20 + (i % 4) * 50, coord_y=80 + (i // 4) * 40,
            ))
    else:
        for i in range(1, total + 1):
            piso = (i - 1) // 5 + 1
            num = 100 * piso + ((i - 1) % 5 + 1)
            out.append(Salon(
                edificio_id=edificio.id,
                codigo=f'{edificio.clave}-{num}',
                nombre=f'Aula {edificio.clave}-{num}',
                tipo='aula', capacidad=35, piso=piso,
                equipamiento=['proyector', 'AC', 'pizarrón'],
                coord_x=20 + ((i - 1) % 5) * 38,
                coord_y=20 + ((i - 1) // 5) * 40,
            ))
    return out


def run():
    app = create_app('desarrollo')
    with app.app_context():
        print('→ Borrando datos previos…')
        db.drop_all()
        print('→ Creando tablas…')
        db.create_all()

        # Plantel
        plantel = Plantel(**PLANTELES_DATA[0])
        db.session.add(plantel)
        db.session.flush()
        print(f'  · Plantel: {plantel.clave}')

        # Carreras
        carreras_by_slug = {}
        for c_data in CARRERAS_DATA:
            c = Carrera(plantel_id=plantel.id, **c_data)
            db.session.add(c)
            db.session.flush()
            carreras_by_slug[c.slug] = c
        print(f'  · Carreras: {len(carreras_by_slug)}')

        # Materias
        materias_by_clave = {}
        total_materias = 0
        for slug, plan in MATERIAS_PLAN.items():
            carrera = carreras_by_slug[slug]
            for sem, materias in plan.items():
                for clave, nombre, tipo, creditos in materias:
                    m = Materia(
                        clave=clave, nombre=nombre,
                        nombre_corto=nombre.split('—')[0].strip()[:80],
                        carrera_id=carrera.id, semestre=sem,
                        tipo=tipo, creditos=creditos,
                        horas_teoria=2 if tipo != 'laboratorio' else 1,
                        horas_practica=2 if tipo == 'laboratorio' else 1,
                    )
                    db.session.add(m)
                    materias_by_clave[clave] = m
                    total_materias += 1
        db.session.flush()
        print(f'  · Materias: {total_materias}')

        # Edificios y salones
        salones_total = 0
        salones_by_codigo = {}
        for e_data in EDIFICIOS_DATA:
            total_s = e_data.pop('salones')
            e = Edificio(plantel_id=plantel.id, **e_data)
            db.session.add(e)
            db.session.flush()
            for s in crear_salones(e, total_s):
                db.session.add(s)
                db.session.flush()
                salones_by_codigo[s.codigo] = s
                salones_total += 1
        print(f'  · Edificios: {len(EDIFICIOS_DATA)} / Salones: {salones_total}')

        # POI
        for poi_data in POI_DATA:
            db.session.add(PuntoInteres(plantel_id=plantel.id, **poi_data))
        print(f'  · Puntos de interés: {len(POI_DATA)}')

        # Periodo activo
        periodo = PeriodoAcademico(
            clave='2026-A', nombre='Primavera 2026',
            plantel_id=plantel.id,
            fecha_inicio=date(2026, 2, 2),
            fecha_fin=date(2026, 7, 3),
            apertura_inscripciones=datetime(2026, 1, 12, 8, 0),
            cierre_inscripciones=datetime(2026, 1, 30, 20, 0),
            activo=True,
        )
        db.session.add(periodo)
        db.session.flush()
        # Calendario
        eventos = [
            ('Inicio de clases', 'evento', date(2026, 2, 2), None, '#172846'),
            ('Día del trabajo', 'feriado', date(2026, 5, 1), None, '#DC3545'),
            ('Parciales 1', 'examen', date(2026, 3, 16), date(2026, 3, 20), '#0D6EFD'),
            ('Vacaciones de Semana Santa', 'vacaciones',
             date(2026, 3, 30), date(2026, 4, 3), '#28A745'),
            ('Parciales 2', 'examen', date(2026, 5, 11), date(2026, 5, 15), '#0D6EFD'),
        ]
        for tit, tipo, fi, ff, col in eventos:
            db.session.add(CalendarioAcademico(
                periodo_id=periodo.id, titulo=tit, tipo=tipo,
                fecha_inicio=fi, fecha_fin=ff, color=col, aplica_a='todos'))
        print(f'  · Periodo activo: {periodo.clave}')

        # Usuarios
        users_by_email = {}
        for u_data in USERS_DATA:
            data = dict(u_data)
            password = data.pop('password')
            slug = data.pop('carrera_slug', None)
            carrera = carreras_by_slug.get(slug) if slug else None
            u = User(plantel_id=plantel.id, estado='activo', **data)
            if carrera:
                u.carrera_id = carrera.id
            u.set_password(password)
            db.session.add(u)
            db.session.flush()
            users_by_email[u.email] = u
        print(f'  · Usuarios: {len(users_by_email)}')

        alvaro = users_by_email['alvaro.diaz@alumnos.udg.mx']

        # Tipos de trámite
        for t_data in TIPOS_TRAMITE_DATA:
            db.session.add(TipoTramite(**t_data))
        db.session.flush()
        print(f'  · Tipos de trámite: {len(TIPOS_TRAMITE_DATA)}')

        # Trámites de muestra
        tipo_constancia = TipoTramite.query.filter_by(
            nombre='Constancia de estudios').first()
        tipo_kardex = TipoTramite.query.filter_by(
            nombre='Kárdex con calificaciones').first()
        admin = users_by_email['admin@udg.mx']

        t1 = Tramite(folio='TRM-2026-00001', solicitante_id=alvaro.id,
                     tipo_tramite_id=tipo_constancia.id, estado='listo',
                     descripcion='Para trámite de beca.',
                     atendido_por=admin.id)
        db.session.add(t1)
        db.session.flush()
        db.session.add(SeguimientoTramite(
            tramite_id=t1.id, estado_anterior=None,
            estado_nuevo='recibido', usuario_id=alvaro.id,
            comentario='Trámite recibido.'))
        db.session.add(SeguimientoTramite(
            tramite_id=t1.id, estado_anterior='recibido',
            estado_nuevo='en_proceso', usuario_id=admin.id,
            comentario='En revisión por servicios escolares.'))
        db.session.add(SeguimientoTramite(
            tramite_id=t1.id, estado_anterior='en_proceso',
            estado_nuevo='listo', usuario_id=admin.id,
            comentario='Listo para entrega en ventanilla.'))

        t2 = Tramite(folio='TRM-2026-00002', solicitante_id=alvaro.id,
                     tipo_tramite_id=tipo_kardex.id, estado='en_proceso',
                     descripcion='Solicito kárdex actualizado.',
                     atendido_por=admin.id)
        db.session.add(t2)
        db.session.flush()
        db.session.add(SeguimientoTramite(
            tramite_id=t2.id, estado_anterior=None,
            estado_nuevo='recibido', usuario_id=alvaro.id,
            comentario='Trámite recibido.'))

        # Horario de Álvaro
        horario_alvaro = Horario(
            user_id=alvaro.id, periodo_id=periodo.id,
            nombre='Horario 4° Informática',
            estado='publicado',
            publicado_at=datetime.utcnow() - timedelta(days=5),
        )
        db.session.add(horario_alvaro)
        db.session.flush()

        for dia, hi, hf, clave, salon_cod, prof_email in ALVARO_BLOQUES:
            materia = materias_by_clave[clave]
            salon = salones_by_codigo[salon_cod]
            profesor = users_by_email[prof_email]
            db.session.add(Bloque(
                horario_id=horario_alvaro.id,
                materia_id=materia.id,
                salon_id=salon.id,
                profesor_id=profesor.id,
                dia=dia,
                hora_inicio=time.fromisoformat(hi),
                hora_fin=time.fromisoformat(hf),
                tipo_sesion='laboratorio' if materia.tipo == 'laboratorio'
                            else 'teoria',
            ))
        db.session.flush()

        # Detectar conflictos en el horario
        from app.utils.conflicts import detectar_conflictos_horario
        en_conflicto = detectar_conflictos_horario(horario_alvaro.id)
        materias_by_id = {m.id: m for m in materias_by_clave.values()}
        creditos_unicos = {b.materia_id for b in horario_alvaro.bloques}
        horario_alvaro.total_creditos = sum(
            materias_by_id[mid].creditos for mid in creditos_unicos)
        horario_alvaro.total_horas = sum(
            int((datetime.combine(date.today(), b.hora_fin) -
                 datetime.combine(date.today(), b.hora_inicio)).total_seconds()
                // 3600) for b in horario_alvaro.bloques)
        print(f'  · Horario de Álvaro publicado con '
              f'{len(en_conflicto)} bloques en conflicto (esperado: 2).')

        # Inscripciones de Álvaro (una por materia única)
        inscripciones_alvaro = []
        for clave in {b.materia.clave for b in horario_alvaro.bloques}:
            materia = materias_by_clave[clave]
            prof = next((b.profesor for b in horario_alvaro.bloques
                         if b.materia_id == materia.id), None)
            ins = Inscripcion(
                estudiante_id=alvaro.id, materia_id=materia.id,
                periodo_id=periodo.id, grupo='A',
                profesor_id=prof.id if prof else None,
                estado='activa',
            )
            db.session.add(ins)
            db.session.flush()
            inscripciones_alvaro.append(ins)

        # Calificaciones de muestra (publicadas)
        califs_data = [
            ('INF-401', 'parcial_1', 8.7),
            ('INF-401', 'parcial_2', 9.0),
            ('INF-402', 'parcial_1', 7.8),
            ('INF-403', 'parcial_1', 9.4),
            ('INF-403', 'parcial_2', 9.1),
            ('INF-404', 'parcial_1', 8.2),
            ('INF-405', 'parcial_1', 8.5),
            ('INF-406', 'parcial_1', 7.5),
        ]
        for clave, tipo, valor in califs_data:
            ins = next((i for i in inscripciones_alvaro
                        if i.materia.clave == clave), None)
            if ins:
                db.session.add(Calificacion(
                    inscripcion_id=ins.id, tipo=tipo, valor=valor,
                    capturado_por=admin.id, publicado=True,
                    publicado_at=datetime.utcnow() - timedelta(days=2),
                ))

        # Asistencia de muestra (4 semanas atrás)
        for ins in inscripciones_alvaro:
            bloques_materia = [b for b in horario_alvaro.bloques
                               if b.materia_id == ins.materia_id]
            for semana in range(4):
                for b in bloques_materia:
                    fecha = (date.today() - timedelta(weeks=semana))
                    estado = 'presente'
                    if semana == 1 and b.dia == 'mar':
                        estado = 'ausente'
                    elif semana == 2 and b.dia == 'jue':
                        estado = 'justificado'
                    db.session.add(RegistroAsistencia(
                        inscripcion_id=ins.id, bloque_id=b.id,
                        fecha=fecha, estado=estado,
                        registrado_por=ins.profesor_id or admin.id,
                    ))

        # Anuncios
        db.session.add(Anuncio(
            autor_id=admin.id, plantel_id=plantel.id,
            titulo='Bienvenida al periodo 2026-A',
            cuerpo='Te damos la bienvenida al nuevo ciclo escolar. '
                   'Revisa tu horario y verifica que no tenga conflictos.',
            audiencia='estudiantes', fijado=True, publicado=True,
            publicado_at=datetime.utcnow() - timedelta(days=10),
        ))
        db.session.add(Anuncio(
            autor_id=admin.id, plantel_id=plantel.id,
            titulo='Cierre de inscripciones próximo',
            cuerpo='Las inscripciones cierran el 30 de enero a las 20:00 h.',
            audiencia='estudiantes', publicado=True,
            publicado_at=datetime.utcnow() - timedelta(days=3),
            expira_at=datetime.utcnow() + timedelta(days=20),
        ))

        # Notificaciones para Álvaro
        for titulo, tipo, cuerpo in [
            ('Tu horario tiene un conflicto',
             'conflicto',
             'Detectamos un cruce el miércoles a las 11:00. Resuélvelo antes '
             'del cierre del periodo.'),
            ('Calificaciones publicadas',
             'calificacion',
             'Se publicaron tus calificaciones del Parcial 1 en varias materias.'),
            ('Trámite TRM-2026-00001 listo',
             'tramite',
             'Tu constancia está lista para recoger en ventanilla.'),
        ]:
            db.session.add(Notificacion(
                destinatario_id=alvaro.id, tipo=tipo,
                titulo=titulo, cuerpo=cuerpo,
                accion_url='/dashboard',
                created_at=datetime.utcnow() - timedelta(hours=2),
            ))

        db.session.commit()
        print('\n✅ Seed completado.')
        print('\nCuentas (todas con contraseña en USERS_DATA):')
        for u in users_by_email.values():
            print(f'   {u.rol:>12s}  ·  {u.email}')


if __name__ == '__main__':
    run()
