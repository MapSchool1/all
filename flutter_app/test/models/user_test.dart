import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/models/user.dart';

void main() {
  group('AppUser', () {
    final fixture = {
      'id': 3,
      'nombre': 'Álvaro',
      'apellido_p': 'Díaz',
      'apellido_m': 'Ramírez',
      'email': 'alvaro.diaz@alumnos.udg.mx',
      'rol': 'estudiante',
      'estado': 'activo',
      'expediente': '218 492',
      'avatar_color': '#3C61A5',
      'semestre_actual': 4,
      'carrera': {'id': 1, 'nombre': 'Tec. Informática'},
    };

    test('fromJson parsea todos los campos', () {
      final u = AppUser.fromJson(fixture);
      expect(u.id, 3);
      expect(u.nombre, 'Álvaro');
      expect(u.apellidoP, 'Díaz');
      expect(u.apellidoM, 'Ramírez');
      expect(u.email, 'alvaro.diaz@alumnos.udg.mx');
      expect(u.rol, 'estudiante');
      expect(u.estado, 'activo');
      expect(u.expediente, '218 492');
      expect(u.avatarColor, '#3C61A5');
      expect(u.semestreActual, 4);
      expect(u.carreraNombre, 'Tec. Informática');
    });

    test('nombreCompleto une nombre + apellidos', () {
      final u = AppUser.fromJson(fixture);
      expect(u.nombreCompleto, 'Álvaro Díaz Ramírez');
    });

    test('nombreCompleto sin apellido_m no incluye espacio extra', () {
      final f = Map<String, dynamic>.from(fixture)..['apellido_m'] = null;
      final u = AppUser.fromJson(f);
      expect(u.nombreCompleto, 'Álvaro Díaz');
    });

    test('iniciales toma primera letra de nombre y apellido_p', () {
      final u = AppUser.fromJson(fixture);
      expect(u.iniciales, 'ÁD');
    });

    test('iniciales con nombre vacío devuelve solo apellido', () {
      final f = Map<String, dynamic>.from(fixture)..['nombre'] = '';
      final u = AppUser.fromJson(f);
      expect(u.iniciales, 'D');
    });

    test('avatarColor por defecto es #172846 si falta', () {
      final f = Map<String, dynamic>.from(fixture)..remove('avatar_color');
      final u = AppUser.fromJson(f);
      expect(u.avatarColor, '#172846');
    });

    test('carrera nula no rompe el parser', () {
      final f = Map<String, dynamic>.from(fixture)..remove('carrera');
      final u = AppUser.fromJson(f);
      expect(u.carreraNombre, isNull);
    });
  });
}
