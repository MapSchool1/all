import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/models/horario.dart';

void main() {
  group('Horario.fromResponse', () {
    final response = {
      'horario': {
        'id': 1,
        'nombre': 'Horario 4° Informática',
        'estado': 'publicado',
        'total_creditos': 36,
        'total_horas': 26,
        'tiene_conflictos': true,
      },
      'bloques': [
        {
          'id': 1, 'dia': 'lun', 'hora_inicio': '07:00', 'hora_fin': '09:00',
          'conflicto': false,
          'materia': {'nombre': 'Cálculo I', 'tipo': 'tronco_comun'},
        },
        {
          'id': 7, 'dia': 'mie', 'hora_inicio': '11:00', 'hora_fin': '13:00',
          'conflicto': true,
          'materia': {'nombre': 'Programación Web', 'tipo': 'laboratorio'},
        },
        {
          'id': 8, 'dia': 'mie', 'hora_inicio': '11:00', 'hora_fin': '13:00',
          'conflicto': true,
          'materia': {'nombre': 'Bases de Datos II', 'tipo': 'area_profesional'},
        },
      ],
    };

    test('parsea metadata del horario', () {
      final h = Horario.fromResponse(response);
      expect(h.id, 1);
      expect(h.nombre, 'Horario 4° Informática');
      expect(h.estado, 'publicado');
      expect(h.totalCreditos, 36);
      expect(h.totalHoras, 26);
      expect(h.tieneConflictos, isTrue);
    });

    test('parsea los 3 bloques', () {
      final h = Horario.fromResponse(response);
      expect(h.bloques.length, 3);
    });

    test('detecta los 2 bloques en conflicto Mié 11:00', () {
      final h = Horario.fromResponse(response);
      final conflictos = h.bloques.where((b) => b.conflicto).toList();
      expect(conflictos.length, 2);
      expect(conflictos.every((b) => b.dia == 'mie'), isTrue);
      expect(conflictos.every((b) => b.horaInicio == '11:00'), isTrue);
    });

    test('nombre por defecto si no viene', () {
      final r = {
        'horario': {
          'id': 99, 'estado': 'borrador',
          'total_creditos': 0, 'total_horas': 0, 'tiene_conflictos': false,
        },
        'bloques': [],
      };
      final h = Horario.fromResponse(r);
      expect(h.nombre, 'Mi horario');
    });

    test('bloques vacío no rompe', () {
      final r = {
        'horario': {
          'id': 1, 'nombre': 'Vacío', 'estado': 'borrador',
          'total_creditos': 0, 'total_horas': 0, 'tiene_conflictos': false,
        },
        'bloques': [],
      };
      final h = Horario.fromResponse(r);
      expect(h.bloques, isEmpty);
    });
  });
}
