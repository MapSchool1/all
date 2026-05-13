import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/models/salon.dart';

void main() {
  group('Salon', () {
    final fixture = {
      'id': 12,
      'codigo': 'LAB-4',
      'nombre': 'Lab. de Programación Web',
      'tipo': 'sala_computo',
      'capacidad': 30,
      'piso': 1,
      'activo': true,
      'disponible_ahora': true,
      'edificio_id': 5,
      'edificio': {'clave': 'LAB', 'nombre': 'Laboratorios'},
    };

    test('fromJson parsea todos los campos', () {
      final s = Salon.fromJson(fixture);
      expect(s.id, 12);
      expect(s.codigo, 'LAB-4');
      expect(s.nombre, 'Lab. de Programación Web');
      expect(s.tipo, 'sala_computo');
      expect(s.capacidad, 30);
      expect(s.piso, 1);
      expect(s.activo, isTrue);
      expect(s.disponibleAhora, isTrue);
      expect(s.edificioId, 5);
      expect(s.edificioClave, 'LAB');
    });

    test('disponibleAhora por defecto es true', () {
      final f = Map<String, dynamic>.from(fixture)..remove('disponible_ahora');
      final s = Salon.fromJson(f);
      expect(s.disponibleAhora, isTrue);
    });

    test('edificioClave es ? si no viene edificio', () {
      final f = Map<String, dynamic>.from(fixture)..remove('edificio');
      final s = Salon.fromJson(f);
      expect(s.edificioClave, '?');
    });

    test('valores por defecto seguros', () {
      final s = Salon.fromJson({
        'id': 1,
        'codigo': 'X-1',
      });
      expect(s.capacidad, 0);
      expect(s.piso, 1);
      expect(s.activo, isTrue);
      expect(s.tipo, isNull);
    });
  });
}
