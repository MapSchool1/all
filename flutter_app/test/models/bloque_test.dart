import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/models/bloque.dart';

void main() {
  group('Bloque', () {
    final fixture = {
      'id': 7,
      'dia': 'mie',
      'hora_inicio': '11:00',
      'hora_fin': '13:00',
      'conflicto': true,
      'materia': {
        'id': 4,
        'nombre': 'Programación Web',
        'nombre_corto': 'Prog. Web',
        'tipo': 'laboratorio',
      },
      'salon': {'id': 12, 'codigo': 'LAB-4'},
      'profesor': {'id': 5, 'nombre_completo': 'Andrea Reyes'},
    };

    test('fromJson parsea todos los campos', () {
      final b = Bloque.fromJson(fixture);
      expect(b.id, 7);
      expect(b.dia, 'mie');
      expect(b.horaInicio, '11:00');
      expect(b.horaFin, '13:00');
      expect(b.conflicto, true);
    });

    test('materiaNombre prefiere nombre_corto sobre nombre', () {
      final b = Bloque.fromJson(fixture);
      expect(b.materiaNombre, 'Prog. Web');
    });

    test('materiaNombre cae a nombre si no hay nombre_corto', () {
      final f = Map<String, dynamic>.from(fixture);
      f['materia'] = {'nombre': 'Programación Web', 'tipo': 'laboratorio'};
      final b = Bloque.fromJson(f);
      expect(b.materiaNombre, 'Programación Web');
    });

    test('materiaNombre devuelve em-dash si no hay materia', () {
      final f = Map<String, dynamic>.from(fixture)..['materia'] = null;
      final b = Bloque.fromJson(f);
      expect(b.materiaNombre, '—');
    });

    test('salonCodigo devuelve em-dash si no hay salon', () {
      final f = Map<String, dynamic>.from(fixture)..['salon'] = null;
      final b = Bloque.fromJson(f);
      expect(b.salonCodigo, '—');
    });

    test('horaInicioH y horaFinH parsean entero correcto', () {
      final b = Bloque.fromJson(fixture);
      expect(b.horaInicioH, 11);
      expect(b.horaFinH, 13);
      expect(b.duracionH, 2);
    });

    test('conflicto por defecto es false si no viene', () {
      final f = Map<String, dynamic>.from(fixture)..remove('conflicto');
      final b = Bloque.fromJson(f);
      expect(b.conflicto, false);
    });

    test('tipoMateria refleja el tipo de la materia', () {
      final b = Bloque.fromJson(fixture);
      expect(b.tipoMateria, 'laboratorio');
    });
  });
}
